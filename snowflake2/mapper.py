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
from aggregation_handler import detect_aggregation, build_aggregation_query, is_percentage_prompt
from followup_handler import is_follow_up_prompt

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

# Load business_mapping.json
business_terms_path = "data/business_mapping.json"
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
    logger.debug(f"Prompt lower: {prompt_lower}")

    # Initialize variables
    table_name = None
    where_clauses = []
    applied_business_terms = []

    # Apply business rules for table selection and conditions
    for key, rule in business_terms.items():
        logger.debug(f"Checking business term: {key}")
        if key in prompt_lower and (not table_name or rule["table"].upper() == table_name):
            col = rule["column"].upper()
            if rule.get("not_null"):
                where_clauses.append(f"{col} IS NOT NULL")
                logger.debug(f"Applied business rule: {col} IS NOT NULL for key {key}")
            elif rule.get("is_null"):
                where_clauses.append(f"{col} IS NULL")
                logger.debug(f"Applied business rule: {col} IS NULL for key {key}")
            elif "value" in rule:
                val = rule["value"]
                val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                where_clauses.append(f"{col} = {val}")
                logger.debug(f"Applied business rule: {col} = {val} for key {key}")
            applied_business_terms.append(key)
            if not table_name:
                table_name = rule["table"].upper()
                logger.debug(f"Selected table {table_name} via business term: {key}")

    # Determine table and metadata if not set by business terms
    if not table_name and matched_table:
        if isinstance(matched_table, str):
            table_name = matched_table.upper()
            metadata = schema_metadata.get(table_name, {})
            if not metadata:
                # Try case-insensitive lookup
                for key in schema_metadata:
                    if key.upper() == table_name:
                        metadata = schema_metadata[key]
                        table_name = key.upper()
                        logger.debug(f"Case-insensitive match for table: {table_name}")
                        break
        elif isinstance(matched_table, dict):
            table_name = list(matched_table.keys())[0].upper()
            metadata = matched_table[table_name]
        else:
            logger.error("Invalid matched_table structure")
            raise Exception("Invalid matched_table structure.")
    elif not table_name:
        logger.error("Could not determine table for prompt")
        raise Exception("❌ Could not determine table for prompt")

    # Fallback to rag_data if metadata is missing
    metadata = schema_metadata.get(table_name, {})
    if not metadata and rag_data:
        for rag_table, rag_meta in rag_data.items():
            if rag_table.upper() == table_name:
                metadata = rag_meta
                logger.debug(f"Using rag_data metadata for table: {table_name}")
                break

    if not metadata:
        logger.error(f"No metadata found for table: {table_name}")
        raise Exception(f"No metadata found for table: {table_name}")

    table_name_upper = table_name.upper()
    columns_meta = metadata.get("columns", {})
    fields = extract_entities(prompt)

    if not applied_business_terms and not is_follow_up_prompt(prompt):
        logger.warning(f"No business terms matched for prompt: {prompt}")

    # Detect aggregation
    force_count = any(kw in prompt_lower for kw in ["how many", "number of"])
    if force_count:
        agg_func = "COUNT"
        agg_col = None
    else:
        try:
            agg_func, agg_col = detect_aggregation(prompt, dict(columns_meta))
        except Exception:
            agg_func, agg_col = None, None
        logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

    # Fallback column for COUNT
    if agg_func == "COUNT" and not agg_col:
        numeric_col = next(
            (col for col, meta in columns_meta.items()
             if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
            None
        )
        agg_col = numeric_col or "*"
        logger.debug(f"Selected COUNT column: {agg_col}")

    # Handle percentage logic
    if agg_func == "PERCENTAGE":
        if not agg_col:
            for key, rule in business_terms.items():
                if key in prompt_lower and rule["table"].upper() == table_name_upper:
                    agg_col = rule["column"].upper()
                    break
        if not agg_col:
            for col, meta in columns_meta.items():
                if isinstance(meta, dict) and meta.get("type") == "boolean":
                    agg_col = col
                    break
        if not agg_col:
            logger.error("Could not infer condition column for percentage query")
            raise Exception("❌ Could not infer condition column for percentage query")

    # Build aggregation query if needed
    if agg_func:
        try:
            query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, dict(columns_meta))
            if where_clauses:
                where_clause = " WHERE " + " AND ".join(where_clauses)
                query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE)
                if "LIMIT" not in query.upper():
                    limit = extract_limit_from_prompt(prompt) or 50
                    query += f" LIMIT {limit}"
            logger.info(f"Generated aggregation SQL: {query}")
            return query
        except Exception as e:
            logger.error(f"Aggregation query failed: {str(e)}")
            raise Exception(f"❌ Aggregation query failed: {str(e)}")

    # Date range logic
    inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
    from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
    to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to

    date_cols = [col for col, meta in columns_meta.items()
                 if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
    if (from_dt or to_dt) and date_cols:
        date_col = date_cols[0].upper()
        if from_dt:
            where_clauses.append(f"{date_col} >= '{from_dt}'")
        if to_dt:
            where_clauses.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

    # Other filters
    try:
        where_clauses += extract_comparative_filters(prompt, dict(columns_meta))
        where_clauses += extract_direct_column_filters(prompt, dict(columns_meta))
        logger.debug(f"Additional filters applied: {where_clauses}")
    except Exception as e:
        logger.error(f"Filter extraction failed: {str(e)}")
        raise Exception(f"❌ Filter extraction failed: {str(e)}")

    # Columns to SELECT
    selected_cols = [col.upper() for col in columns_meta.keys()]
    query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    else:
        logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
    query += f" LIMIT {limit or extract_limit_from_prompt(prompt) or 50}"
    logger.info(f"Generated SQL: {query}")
    return query









