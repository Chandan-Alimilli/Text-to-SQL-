
import re
import json
import spacy
import os
from datetime import datetime
from dateutil import parser
import logging

from mapper_utils import (
    extract_entities,
    extract_direct_column_filters,
    extract_comparative_filters,
    parse_date_range_from_prompt,
    normalize_text
)
from prompt_utils import extract_limit_from_prompt
from rag_retriever import schema_metadata
from aggregation_handler import detect_aggregation, build_aggregation_query
import auto_progress

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

# Load business_mapping.json
business_terms_path = "business_mapping.json"
business_terms = {}
if os.path.exists(business_terms_path):
    try:
        with open(business_terms_path, "r") as f:
            business_content = f.read().strip()
            if business_content:
                business_terms = json.loads(business_content)
                logger.debug("Successfully loaded business_mapping.json")
                logger.debug(f"Business terms keys: {list(business_terms.keys())}")
            else:
                logger.error("business_mapping.json is empty")
    except Exception as e:
        logger.error(f"Error loading business_mapping.json: {str(e)}")
else:
    logger.error(f"Business mapping file not found: {business_terms_path}")

def generate_sql_query(prompt, matched_table=None, matched_metadata=None, rag_data=None, schema_metadata=schema_metadata, from_date=None, to_date=None, limit=None, memory_context=None):
    """Generate SQL query from prompt, prioritizing business term mappings."""
    prompt_lower = prompt.lower()
    logger.debug(f"Generating SQL for prompt: {prompt_lower}")

    # Initialize variables
    table_name = None
    where_clauses = []
    aggregation_conditions = []  # Store multiple business terms and filters for aggregation
    percentage_condition = None
    percentage_denominator_condition = None  # For queries like "booked over approved"

    # Handle negated and regular business terms
    for key, rule in business_terms.items():
        logger.debug(f"Checking business term: {key}")
        negated = False
        term_match = key
        if "non " + key in prompt_lower or "not " + key in prompt_lower:
            negated = True
            term_match = "non " + key if "non " + key in prompt_lower else "not " + key
        if term_match in prompt_lower:
            col = rule["column"].upper()
            if not table_name:
                table_name = rule["table"].upper()
            elif rule["table"].upper() != table_name:
                logger.warning(f"Multiple tables detected for business terms: {table_name} vs {rule['table'].upper()}")
                continue  # Skip if table mismatch
            if rule.get("not_null"):
                condition = f"{col} IS NOT NULL"
                aggregation_conditions.append(condition)
                logger.debug(f"Applied business rule: {condition} for key {key}")
            elif rule.get("is_null"):
                condition = f"{col} IS NULL"
                aggregation_conditions.append(condition)
                logger.debug(f"Applied business rule: {condition} for key {key}")
            elif "value" in rule:
                val = rule["value"]
                val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
                    if val == "'1'":
                        val = "'0'"
                    elif val == "'0'":
                        val = "'1'"
                    else:
                        stripped_val = val.strip("'")
                        val = f"'Not {stripped_val}'"
                condition = f"{col} = {val}"
                aggregation_conditions.append(condition)
                logger.debug(f"Applied business rule: {condition} for key {term_match}")
            if not table_name:
                table_name = rule["table"].upper()
                logger.debug(f"Selected table {table_name} via business term: {key}")

    # Detect percentage with optional "over" clause
    percentage_match = re.search(r"what is the percentage of ([\w\s]+?)(?: applications)?(?:\s+over\s+([\w\s]+?)(?: applications)?)?", prompt_lower)
    if percentage_match:
        numerator_terms = percentage_match.group(1).strip().split()
        denominator_term = percentage_match.group(2)
        for term in numerator_terms:
            rule = business_terms.get(term)
            if rule and rule["table"].upper() == table_name:
                col = rule["column"].upper()
                val = str(rule["value"]).upper() if isinstance(rule["value"], bool) or rule["value"] in ["0", "1"] else f"'{rule['value']}'"
                condition = f"{col} = {val}"
                if not percentage_condition:
                    percentage_condition = condition
                else:
                    percentage_condition = f"{percentage_condition} AND {condition}"
                logger.debug(f"Added to percentage condition: {condition}")
        if denominator_term:
            rule = business_terms.get(denominator_term.strip())
            if rule and rule["table"].upper() == table_name:
                col = rule["column"].upper()
                val = str(rule["value"]).upper() if isinstance(rule["value"], bool) or rule["value"] in ["0", "1"] else f"'{rule['value']}'"
                percentage_denominator_condition = f"{col} = {val}"
                logger.debug(f"Set denominator condition: {percentage_denominator_condition}")
        elif not percentage_denominator_condition:
            percentage_denominator_condition = None  # Default to total count

    # Determine table and metadata if not set by business terms
    if not table_name and matched_table:
        if isinstance(matched_table, str):
            table_name = matched_table.upper()
            metadata = schema_metadata.get(table_name, {})
            if not metadata:
                for key in schema_metadata:
                    if key.upper() == table_name:
                        metadata = schema_metadata[key]
                        table_name = key.upper()
                        logger.debug(f"Case-insensitive match for table: {table_name}")
                        break
                if not metadata and rag_data:
                    for rag_table in rag_data:
                        if rag_table.upper() == table_name:
                            metadata = rag_data[rag_table]
                            table_name = rag_table.upper()
                            logger.debug(f"Fallback to rag_data for table: {table_name}")
                            break
        elif isinstance(matched_table, dict):
            table_name = list(matched_table.keys())[0].upper()
            metadata = matched_table[table_name]
        else:
            logger.error("Invalid matched_table structure")
            raise Exception("Invalid matched_table structure.")
    elif not table_name and memory_context:
        for mem in reversed(memory_context[-3:]):
            last_sql = mem.get("sql", "")
            table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1).upper()
                metadata = schema_metadata.get(table_name, {})
                if metadata:
                    logger.debug(f"Inferred table {table_name} from memory context")
                    break
    if not table_name:
        logger.error("Could not determine table for prompt")
        raise Exception("❌ Could not determine table for prompt")

    # Ensure metadata is valid
    metadata = schema_metadata.get(table_name, {})  # Single table only
    if not metadata and rag_data:
        for rag_table, rag_meta in rag_data.items():
            if rag_table.upper() == table_name:
                metadata = rag_meta
                logger.debug(f"Using rag_data metadata for table: {table_name}")
                break
    if not metadata:
        logger.error(f"No metadata found for table: {table_name}")
        raise Exception(f"No metadata found for table: {table_name}")

    table_name_upper = table_name
    columns_meta = metadata.get("columns", {})
    fields = extract_entities(prompt)

    if not aggregation_conditions and not percentage_condition:
        logger.warning(f"No business terms or percentage conditions matched for prompt: {prompt}")

    # Detect aggregation
    force_count = any(kw in prompt_lower for kw in ["how many", "number of", "count of"])
    force_sum = any(kw in prompt_lower for kw in ["sum of", "total"])
    if force_count:
        agg_func = "COUNT"
        agg_col = None
    elif force_sum:
        agg_func = "SUM"
        agg_col = None
    else:
        try:
            agg_func, agg_col = detect_aggregation(prompt, columns_meta)
        except Exception:
            agg_func, agg_col = None, None
        logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

    # Fallback column for COUNT and SUM
    if agg_func in ["COUNT", "SUM"]:
        if not agg_col:
            if agg_func == "COUNT":
                agg_col = next(
                    (col for col, meta in columns_meta.items()
                     if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
                    "ACCT_NB"
                )
                logger.debug(f"Selected COUNT column: {agg_col}")
            elif agg_func == "SUM":
                for col, meta in columns_meta.items():
                    if isinstance(meta, dict) and meta.get("type") == "numeric":
                        if col.lower() in prompt_lower or meta.get("desc", "").lower() in prompt_lower:
                            agg_col = col
                            break
                agg_col = agg_col or next(
                    (col for col, meta in columns_meta.items()
                     if isinstance(meta, dict) and meta.get("type") == "numeric"),
                    None
                )
                logger.debug(f"Selected SUM column: {agg_col}")

    # Handle percentage logic with multiple conditions
    if agg_func == "PERCENTAGE":
        if not percentage_condition and aggregation_conditions:
            percentage_condition = " AND ".join(aggregation_conditions)
            logger.debug(f"Combined multiple business terms: {percentage_condition}")
        # Add additional filters if present
        comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
        direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
        comparative_filters = list(comparative_filters)
        direct_filters = list(direct_filters)
        all_filters = comparative_filters + direct_filters
        if all_filters:
            percentage_condition = f"{percentage_condition} AND {' AND '.join(all_filters)}" if percentage_condition else " AND ".join(all_filters)
            logger.debug(f"Percentage condition with filters: {percentage_condition}")

    # Date range logic
    inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
    from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
    to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to
    date_cols = [col for col, meta in columns_meta.items()
                 if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
    date_col = date_cols[0].upper() if date_cols else None
    if (from_dt or to_dt) and date_col:
        if from_dt and to_dt:
            where_clauses.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        else:
            if from_dt:
                where_clauses.append(f"{date_col} >= '{from_dt}'")
            if to_dt:
                where_clauses.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

    # Extract additional filters for non-percentage queries or additional conditions
    try:
        comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
        direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
        additional_filters = comparative_filters + direct_filters
        additional_filters = list(dict.fromkeys(additional_filters))  # Remove duplicates
        if agg_func != "PERCENTAGE":
            where_clauses += aggregation_conditions + additional_filters  # Include all conditions
            logger.debug(f"Applied filters for non-percentage query: {where_clauses}")
        elif agg_func == "PERCENTAGE" and percentage_condition and not percentage_denominator_condition:
            # Exclude percentage_condition from where_clauses
            percentage_conditions = set(percentage_condition.split(" AND ")) if percentage_condition else set()
            additional_filters = [f for f in additional_filters if f not in percentage_conditions]
            if additional_filters:
                where_clauses += additional_filters
                logger.debug(f"Additional filters for PERCENTAGE query: {additional_filters}")
    except Exception as e:
        logger.error(f"Filter extraction failed: {str(e)}")
        raise Exception(f"❌ Filter extraction failed: {str(e)}")

    # Extract limit from prompt
    extracted_limit = extract_limit_from_prompt(prompt)

    # Build aggregation query
    if agg_func:
        try:
            query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, columns_meta, percentage_condition, percentage_denominator_condition)
            if where_clauses:
                where_clause = " WHERE " + " AND ".join(where_clauses)
                query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE) or query + where_clause
            if "LIMIT" not in query.upper():
                # Apply explicit limit if specified, otherwise apply default limit only if no date range
                if extracted_limit != 50:  # 50 is the default limit in prompt_utils
                    query += f" LIMIT {extracted_limit}"
                elif not (from_dt or to_dt):
                    query += f" LIMIT {limit or 50}"
            logger.info(f"Generated aggregation SQL: {query}")
            return query
        except Exception as e:
            logger.error(f"Aggregation query failed: {str(e)}")
            raise Exception(f"❌ Aggregation query failed: {str(e)}")
    else:
        # Explicitly check for auto progress request with improved detection
        progress_query = auto_progress.build_progress_query(prompt, schema_metadata, business_terms)
        if progress_query:
            logger.info(f"Generated progress SQL: {progress_query}")
            return progress_query

    # Default SELECT query
    selected_cols = [col.upper() for col in columns_meta.keys()]
    query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    else:
        logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
    # Apply explicit limit if specified, otherwise apply default limit only if no date range
    if extracted_limit != 50:  # 50 is the default limit in prompt_utils
        query += f" LIMIT {extracted_limit}"
    elif not (from_dt or to_dt):
        query += f" LIMIT {limit or 50}"
    logger.info(f"Generated SQL: {query}")
    return query