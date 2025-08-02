import re
import logging
import sys
import json
import os
from datetime import datetime
from dateutil import parser
from mapper_utils import (
    extract_entities,
    extract_direct_column_filters,
    extract_comparative_filters,
    parse_date_range_from_prompt,
    normalize_text
)
from rag_retriever import schema_metadata
from prompt_utils import extract_limit_from_prompt
from aggregation_handler import detect_aggregation, build_aggregation_query

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

MAX_MEMORY = 1  # Store only the last effective query
FOLLOWUP_KEYWORDS = ["followback", "follow up", "follow", "back"]

# Load business_mapping.json
business_terms_path = "business_mapping.json"
business_terms = {}
if os.path.exists(business_terms_path):
    try:
        with open(business_terms_path, "r") as f:
            business_content = f.read().strip()
            if business_content:
                business_terms = json.loads(business_content)
                logger.debug(f"Business terms loaded: {list(business_terms.keys())}")
            else:
                logger.error("business_mapping.json is empty")
    except Exception as e:
        logger.error(f"Error loading business_mapping.json: {e}")
else:
    logger.error(f"Business mapping file not found: {business_terms_path}")

def is_follow_up_prompt(prompt):
    """Check if the prompt is a follow-up query."""
    if not prompt:
        logger.debug("Empty prompt received")
        return False
    prompt_lower = prompt.lower()
    result = any(keyword in prompt_lower for keyword in FOLLOWUP_KEYWORDS)
    logger.debug(f"Follow-up detection: prompt='{prompt}', lowercased='{prompt_lower}', keywords={FOLLOWUP_KEYWORDS}, result={result}")
    return result

def get_followup_query(prompt, memory_context):
    """Generate SQL query for follow-up prompt based on previous context."""
    logger.info(f"Processing follow-up prompt: '{prompt}'")
    if not is_follow_up_prompt(prompt):
        logger.warning("Prompt is not a follow-up")
        return None
    if not memory_context:
        logger.warning("No memory context available")
        return None

    # Get the last effective query's context
    mem = memory_context[-1]
    last_prompt = mem.get("prompt", "").lower()
    last_sql = mem.get("sql", "")
    table_name = mem.get("table_name", "").lower()
    schema = mem.get("schema", {})
    last_filters = mem.get("filters", [])

    logger.debug(f"Memory context: prompt='{last_prompt}', sql='{last_sql}', table='{table_name}', filters={last_filters}, schema_columns={schema.get('columns', {}).keys()}")

    # Validate table and schema
    if not table_name:
        logger.error("No table name in memory context")
        return None
    if not schema or not schema.get("columns"):
        logger.error(f"Invalid schema for table '{table_name}': {schema}")
        return None

    # Handle schema_metadata mismatch
    if table_name.upper() not in schema_metadata and table_name not in schema_metadata:
        logger.warning(f"Table {table_name} not in schema_metadata, using RAG-provided schema")
        schema_metadata[table_name] = schema

    columns = schema.get("columns", {})
    logger.debug(f"Using schema columns: {columns.keys()}")

    # Extract previous WHERE clause or use stored filters
    where_match = re.search(r"\bWHERE\b(.+?)(?:LIMIT|ORDER|$)", last_sql, re.IGNORECASE)
    prev_where_clause = where_match.group(1).strip() if where_match else ""
    prev_filters = last_filters if last_filters else [prev_where_clause] if prev_where_clause else []
    logger.debug(f"Previous filters: {prev_filters}")

    # Detect aggregation
    agg_func, agg_col = None, None
    try:
        agg_func, agg_col = detect_aggregation(prompt, columns)
        logger.debug(f"Detected aggregation: {agg_func} on column {agg_col}")
    except Exception as e:
        logger.debug(f"No aggregation detected or error: {e}")
        # Fallback for vague aggregation prompts
        if any(kw in prompt.lower() for kw in ["count of them", "how many", "number of"]):
            agg_func = "COUNT"
            agg_col = next(
                (col for col, meta in columns.items() if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
                "ACCT_NB"
            )
            logger.debug(f"Fallback to COUNT with column: {agg_col}")

    # Check for detail request after aggregation
    is_detail_request = any(kw in prompt.lower() for kw in ["show those", "those applications", "show only", "details", "records"])
    was_previous_aggregation = re.search(r"SELECT\s+(COUNT|SUM|AVG|MAX|MIN|ROUND)", last_sql, re.IGNORECASE)

    # Initialize SQL and conditions
    conditions = []
    percentage_condition = None
    percentage_denominator_condition = None

    # Extract new filters
    logger.debug(f"Extracting filters for prompt '{prompt}' with columns {columns.keys()}")
    direct_filters = extract_direct_column_filters(prompt, columns)
    logger.debug(f"Direct filters extracted: {direct_filters}")
    comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns)
    logger.debug(f"Comparative filters extracted: {comparative_filters}, affected columns: {filtered_columns}")
    conditions.extend(direct_filters)
    conditions.extend(comparative_filters)

    # Handle business terms with exact matching
    prompt_lower = prompt.lower()
    matched_terms = []
    for term, rule in business_terms.items():
        negated = False
        term_match = term
        if f"non {term}" in prompt_lower or f"not {term}" in prompt_lower:
            negated = True
            term_match = f"non {term}" if f"non {term}" in prompt_lower else f"not {term}"
        if re.search(r'\b' + re.escape(term_match) + r'\b', prompt_lower) and rule["table"].lower() == table_name:
            matched_terms.append((term, rule, negated, term_match))

    for term, rule, negated, term_match in matched_terms:
        col = rule["column"].upper()
        if rule.get("not_null"):
            conditions.append(f"{col} IS NOT NULL")
            logger.debug(f"Added filter: {col} IS NOT NULL for term '{term_match}'")
        elif rule.get("is_null"):
            conditions.append(f"{col} IS NULL")
            logger.debug(f"Added filter: {col} IS NULL for term '{term_match}'")
        elif "value" in rule:
            val = rule["value"]
            val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
            if negated and term in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined", "state-allowed", "state-notallowed"]:
                if val == "'1'":
                    val = "'0'"
                elif val == "'0'":
                    val = "'1'"
                else:
                    stripped_val = val.strip("'")
                    val = f"'Not {stripped_val}'"
            conditions.append(f"{col} = {val}")
            logger.debug(f"Added filter: {col} = {val} for term '{term_match}'")

    # Handle date range
    has_new_date_filter = False
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    date_cols = [col for col in columns if isinstance(columns[col], dict) and columns[col].get("type") in ("date", "timestamp")]
    if from_dt and to_dt and date_cols:
        date_col = date_cols[0].upper()
        conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        has_new_date_filter = True
        logger.debug(f"Added new date filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
    elif from_dt and date_cols:
        date_col = date_cols[0].upper()
        conditions.append(f"{date_col} >= '{from_dt}'")
        has_new_date_filter = True
        logger.debug(f"Added new date filter: {date_col} >= '{from_dt}'")
    elif to_dt and date_cols:
        date_col = date_cols[0].upper()
        conditions.append(f"{date_col} <= '{to_dt}'")
        has_new_date_filter = True
        logger.debug(f"Added new date filter: {date_col} <= '{to_dt}'")

    # Special handling for "last month"
    if "last month" in prompt_lower:
        current_date = datetime.now()
        last_month = current_date.replace(day=1, month=current_date.month - 1 if current_date.month > 1 else 12, year=current_date.year - 1 if current_date.month == 1 else current_date.year)
        from_dt = last_month.replace(day=1).strftime("%Y-%m-%d")
        to_dt = last_month.replace(day=31).strftime("%Y-%m-%d")
        if date_cols:
            date_col = date_cols[0].upper()
            conditions = [f for f in conditions if not ("SNPST_DT" in f or "APPL_INIT_DT" in f or "APPL_INIT_TS" in f)]
            conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            has_new_date_filter = True
            logger.debug(f"Added last month filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")

    # Special handling for "current month"
    if "this month" in prompt_lower or "current month" in prompt_lower:
        current_date = datetime.now()
        from_dt = current_date.replace(day=1).strftime("%Y-%m-%d")
        to_dt = current_date.replace(day=31).strftime("%Y-%m-%d")
        if date_cols:
            date_col = date_cols[0].upper()
            conditions = [f for f in conditions if not ("SNPST_DT" in f or "APPL_INIT_DT" in f or "APPL_INIT_TS" in f)]
            conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            has_new_date_filter = True
            logger.debug(f"Added current month filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")

    # Handle percentage queries
    percentage_match = re.search(r"percentage of (?:them|those)(?:\s+out of\s+all of the month)?", prompt_lower)
    if percentage_match and date_cols:
        date_col = date_cols[0].upper()
        current_date = datetime.now()
        month_start = current_date.replace(day=1).strftime("%Y-%m-%d")
        month_end = current_date.replace(day=31).strftime("%Y-%m-%d")
        percentage_denominator_condition = f"{date_col} BETWEEN '{month_start}' AND '{month_end}'"
        logger.debug(f"Set percentage denominator: {percentage_denominator_condition}")
        agg_func = "PERCENTAGE"
        agg_col = next(
            (col for col, meta in columns.items() if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
            "ACCT_NB"
        )

    # Combine filters: Retain all previous filters unless explicitly overridden
    all_filters = []
    prompt_terms = set(extract_entities(prompt_lower) + prompt_lower.split())
    relevant_prev_filters = []
    for f in prev_filters:
        conditions_in_filter = [cond.strip() for cond in f.split(" AND ") if cond.strip()]
        for cond in conditions_in_filter:
            if has_new_date_filter and ("SNPST_DT" in cond or "APPL_INIT_DT" in cond or "APPL_INIT_TS" in cond):
                logger.debug(f"Dropping previous date condition '{cond}' due to new date filter")
                continue
            relevant_prev_filters.append(cond)
            logger.debug(f"Retained previous condition: '{cond}'")
    if relevant_prev_filters:
        all_filters.extend(relevant_prev_filters)
        logger.debug(f"Retained relevant previous filters: {relevant_prev_filters}")
    if conditions:
        all_filters.extend(conditions)
    all_filters = list(dict.fromkeys(all_filters))  # Remove duplicates
    logger.debug(f"All filters: {all_filters}")

    # Store filters for next follow-up
    updated_filters = all_filters

    # Handle percentage conditions for aggregation
    if agg_func == "PERCENTAGE":
        percentage_condition = " AND ".join(all_filters) if all_filters else None
        logger.debug(f"Set percentage condition: {percentage_condition}")

    # Handle aggregation
    if agg_func:
        try:
            if not agg_col and agg_func in ["COUNT", "SUM"]:
                if agg_func == "COUNT":
                    agg_col = next(
                        (col for col, meta in columns.items() if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
                        "ACCT_NB"
                    )
                elif agg_func == "SUM":
                    agg_col = next(
                        (col for col, meta in columns.items() if isinstance(meta, dict) and meta.get("type") == "numeric"),
                        None
                    )
            where_clause = f" WHERE {' AND '.join(all_filters)}" if all_filters else ""
            sql = build_aggregation_query(agg_func, agg_col, table_name, prompt, columns, percentage_condition, percentage_denominator_condition)
            if where_clause and not re.search(r"\bWHERE\b", sql, re.IGNORECASE):
                sql += where_clause
            limit = extract_limit_from_prompt(prompt)
            sql = re.sub(r"\bLIMIT\s+\d+", "", sql, re.IGNORECASE).strip() + f" LIMIT {limit}"
            logger.info(f"Generated follow-up aggregation SQL: '{sql}'")
            add_to_memory(memory_context, prompt, sql, table_name, schema, updated_filters)
            return sql
        except Exception as e:
            logger.error(f"Failed to build aggregation query: {e}", exc_info=True)
            return None

    # Build SELECT query for non-aggregation
    if is_detail_request and was_previous_aggregation:
        logger.debug("Switching from aggregation to detail query")
        sql = f"SELECT {', '.join(columns.keys())} FROM {table_name}"
    else:
        sql = f"SELECT {', '.join(columns.keys())} FROM {table_name}"
    if all_filters:
        sql += f" WHERE {' AND '.join(all_filters)}"
    limit = extract_limit_from_prompt(prompt)
    sql += f" LIMIT {limit}"
    logger.info(f"Generated follow-up SQL: '{sql}'")
    add_to_memory(memory_context, prompt, sql, table_name, schema, updated_filters)
    return sql

def add_to_memory(memory, prompt, sql, table_name, schema, filters=None):
    """Append prompt, SQL, table, schema, and filters to memory context."""
    memory.append({
        "prompt": prompt,
        "sql": sql,
        "table_name": table_name.lower(),
        "schema": schema,
        "filters": filters or []
    })
    if len(memory) > MAX_MEMORY:
        memory.pop(0)
    logger.debug(f"Updated memory: {memory}")