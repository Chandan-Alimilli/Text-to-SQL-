import re
import logging
import sys
import json
import os
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
FOLLOWUP_KEYWORDS = ["follow back", "follow", "back"]

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
        logger.debug(f"No aggregation detected: {e}")

    # Check for detail request after aggregation
    is_detail_request = any(kw in prompt.lower() for kw in ["show those", "those applications", "show only", "details", "records"])
    was_previous_aggregation = re.search(r"SELECT\s+COUNT|SUM|AVG|MAX|MIN", last_sql, re.IGNORECASE)

    # Initialize SQL
    sql = f"SELECT {', '.join(columns.keys())} FROM {table_name}"

    # Extract new filters
    new_filters = []
    logger.debug(f"Passing prompt '{prompt}' and columns {columns.keys()} to extract_direct_column_filters")
    direct_filters = extract_direct_column_filters(prompt, columns)
    logger.debug(f"Direct filters extracted: {direct_filters}")
    comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns)
    logger.debug(f"Comparative filters extracted: {comparative_filters}, affected columns: {filtered_columns}")
    new_filters.extend(direct_filters)
    new_filters.extend(comparative_filters)

    # Fallback for business terms (aligned with mapper.py)
    prompt_lower = prompt.lower()
    if not new_filters:
        logger.warning(f"No filters extracted, applying fallback for business terms: {list(business_terms.keys())}")
        for term, rule in business_terms.items():
            negated = False
            term_match = term
            if f"non {term}" in prompt_lower or f"not {term}" in prompt_lower:
                negated = True
                term_match = f"non {term}" if f"non {term}" in prompt_lower else f"not {term}"
            if term_match in prompt_lower and rule["table"].lower() == table_name:
                col = rule["column"].upper()
                if "value" in rule:
                    val = rule["value"]
                    val = str(val).upper() if isinstance(val, (bool, int)) and val in [0, 1] else f"'{val}'"
                    if negated and term in ["eligible", "non_eligible", "approved", "rejected", "booked", "declined", "state-allowed", "state-notallowed"]:
                        if val == "'1'":
                            val = "'0'"
                        elif val == "'0'":
                            val = "'1'"
                        else:
                            stripped_val = val.strip("'")
                            val = f"'Not {stripped_val}'"
                    new_filters.append(f"{col} = {val}")
                    logger.debug(f"Fallback: Added filter {col} = {val} for term '{term_match}'")

    # Handle date range
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    date_cols = [col for col in columns if isinstance(columns[col], dict) and columns[col].get("type") in ("date", "timestamp")]
    if from_dt and to_dt and date_cols:
        date_col = date_cols[0].upper()
        new_filters.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        logger.debug(f"Added new date filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
    elif from_dt and date_cols:
        date_col = date_cols[0].upper()
        new_filters.append(f"{date_col} >= '{from_dt}'")
        logger.debug(f"Added new date filter: {date_col} >= '{from_dt}'")
    elif to_dt and date_cols:
        date_col = date_cols[0].upper()
        new_filters.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Added new date filter: {date_col} <= '{to_dt}'")

    # Combine filters: Retain relevant previous filters
    all_filters = []
    has_new_date_filter = any("SNPST_DT" in f or "APPL_INIT_DT" in f or "APPL_INIT_TS" in f for f in new_filters)
    prompt_terms = set(extract_entities(prompt_lower) + prompt_lower.split())
    relevant_prev_filters = []
    for f in prev_filters:
        # Split filter into individual conditions
        conditions = [cond.strip() for cond in f.split(" AND ") if cond.strip()]
        for cond in conditions:
            mentioned_columns = [col for col in columns if col.lower() in cond.lower() and any(col.lower() in term for term in prompt_terms)]
            mentioned_terms = [term for term in business_terms if term in prompt_lower and business_terms[term]["column"].lower() in cond.lower()]
            if mentioned_columns or mentioned_terms or (not has_new_date_filter and ("SNPST_DT" in cond or "APPL_INIT_DT" in cond or "APPL_INIT_TS" in cond)):
                relevant_prev_filters.append(cond)
            else:
                logger.debug(f"Dropping previous condition '{cond}' as it doesn't align with prompt terms")
    if relevant_prev_filters:
        all_filters.extend(relevant_prev_filters)
        logger.debug(f"Retained relevant previous filters: {relevant_prev_filters}")
    if new_filters:
        all_filters.extend(new_filters)
    all_filters = list(dict.fromkeys(all_filters))  # Remove duplicates
    logger.debug(f"All filters: {all_filters}")

    # Store filters for next follow-up
    updated_filters = all_filters

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
            sql = build_aggregation_query(agg_func, agg_col, table_name, prompt, columns)
            if where_clause:
                if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
                    sql = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, sql, flags=re.IGNORECASE)
                else:
                    sql += where_clause
            limit = extract_limit_from_prompt(prompt)
            sql = re.sub(r"\bLIMIT\s+\d+", "", sql, re.IGNORECASE).strip() + f" LIMIT {limit}"
            logger.info(f"Generated follow-up aggregation SQL: '{sql}'")
            add_to_memory(memory_context, prompt, sql, table_name, schema, updated_filters)
            return sql
        except Exception as e:
            logger.error(f"Failed to build aggregation query: {e}")
            return None

    # Build SELECT query for non-aggregation
    if is_detail_request and was_previous_aggregation:
        logger.debug("Switching from aggregation to detail query")
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