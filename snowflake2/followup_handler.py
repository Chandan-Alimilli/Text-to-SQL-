# import re
# import logging
# from mapper_utils import (
#     extract_entities,
#     extract_direct_column_filters,
#     extract_comparative_filters,
#     parse_date_range_from_prompt,
#     normalize_text
# )
# from rag_retriever import schema_metadata
# from prompt_utils import extract_limit_from_prompt
# from aggregation_handler import detect_aggregation, build_aggregation_query, is_percentage_prompt

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# MAX_MEMORY = 5

# # Enhanced follow-up trigger phrases
# FOLLOWUP_KEYWORDS = [
#     "show from above", "those", "them", "again", "only those", "just those",
#     "from earlier", "refine", "filter those", "in context", "previous data",
#     "based on above", "give me those", "those entries", "those applications",
#     "can I see", "again please", "from previous result", "follow up",
#     "carry over", "now show", "more on those", "apply to those",
#     "same records", "previous ones", "those results", "revisit those",
#     "filter previous", "from that", "keep those", "show again",
#     "based on last", "same ones", "narrow down those"
# ]

# def is_follow_up_prompt(prompt):
#     """Check if the prompt is a follow-up query."""
#     prompt_lower = normalize_text(prompt).lower()
#     result = any(key in prompt_lower for key in FOLLOWUP_KEYWORDS)
#     logger.debug(f"Follow-up prompt detected: {result} for prompt: {prompt}")
#     return result

# def get_followup_query(prompt, memory_context):
#     """Generate SQL query for follow-up prompt based on previous context."""
#     prompt_lower = prompt.lower()
#     prompt_norm = normalize_text(prompt)
#     if not is_follow_up_prompt(prompt_lower) or not memory_context:
#         logger.warning("No follow-up detected or no memory context available")
#         return None

#     # Iterate over recent memory (last MAX_MEMORY entries)
#     for mem in reversed(memory_context[-MAX_MEMORY:]):
#         last_prompt = mem.get("prompt", "").lower()
#         last_sql = mem.get("sql", "")
#         logger.debug(f"Processing memory: prompt={last_prompt}, sql={last_sql}")

#         # Extract table name from previous SQL
#         table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
#         table = table_match.group(1).upper() if table_match else None
#         if not table or table not in schema_metadata:
#             logger.warning(f"Invalid table {table} or not in schema_metadata")
#             continue

#         columns = schema_metadata[table]["columns"]

#         # Detect if the follow-up is an aggregation query
#         try:
#             agg_func, agg_col = detect_aggregation(prompt, columns)
#             logger.debug(f"Detected aggregation: {agg_func} on column {agg_col}")
#         except Exception as e:
#             agg_func, agg_col = None, None
#             logger.debug(f"No aggregation detected: {e}")

#         # Extract previous WHERE clause
#         where_match = re.search(r"\bWHERE\b(.+?)(?:LIMIT|ORDER|$)", last_sql, re.IGNORECASE)
#         prev_where_clause = where_match.group(1).strip() if where_match else ""
#         logger.debug(f"Previous WHERE clause: {prev_where_clause}")

#         # Extract new filters from current prompt
#         new_filters = []
#         new_filters += extract_direct_column_filters(prompt, columns)
#         new_filters += extract_comparative_filters(prompt, columns)

#         # Handle date range (consistent with mapper_utils)
#         from_dt, to_dt = parse_date_range_from_prompt(prompt)
#         date_cols = [col for col in columns if isinstance(columns[col], dict) and columns[col].get("type") in ("date", "timestamp")]
#         if from_dt and to_dt and date_cols:
#             date_col = date_cols[0].upper()
#             new_filters.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
#             logger.debug(f"Added date filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")

#         # Combine filters
#         all_filters = []
#         if prev_where_clause:
#             all_filters.append(f"({prev_where_clause})")
#         if new_filters:
#             all_filters.append(" AND ".join(new_filters))

#         # Handle aggregation follow-up
#         if agg_func:
#             try:
#                 # Build aggregation query with combined filters
#                 where_clause = " WHERE " + " AND ".join(all_filters) if all_filters else ""
#                 sql = build_aggregation_query(agg_func, agg_col, table, prompt, columns)
#                 # Replace the default WHERE clause with combined filters
#                 if where_clause:
#                     sql = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, sql, flags=re.IGNORECASE)
#                     if "LIMIT" not in sql.upper():
#                         limit = extract_limit_from_prompt(prompt)
#                         sql += f" LIMIT {limit}"
#                 logger.info(f"Generated follow-up aggregation SQL: {sql}")
#                 return sql
#             except Exception as e:
#                 logger.error(f"Failed to build aggregation query: {e}")
#                 continue

#         # Default to SELECT query for non-aggregation follow-ups
#         all_cols = ", ".join(columns.keys())
#         new_sql = f"SELECT {all_cols} FROM {table}"

#         if all_filters:
#             new_sql += " WHERE " + " AND ".join(all_filters)

#         # Add LIMIT
#         limit = extract_limit_from_prompt(prompt)
#         if limit:
#             new_sql += f" LIMIT {limit}"
#         elif "LIMIT" in last_sql.upper():
#             last_limit = re.search(r"LIMIT\s+\d+", last_sql, re.IGNORECASE)
#             if last_limit:
#                 new_sql += f" {last_limit.group()}"
#         logger.info(f"Generated follow-up SQL: {new_sql}")
#         return new_sql

#     logger.warning("No valid follow-up SQL generated from memory context")
#     return None

# def add_to_memory(memory, prompt, sql):
#     """Append prompt and SQL to memory context."""
#     memory.append({
#         "prompt": prompt,
#         "sql": sql
#     })
#     if len(memory) > MAX_MEMORY:
#         memory.pop(0)
#     logger.debug(f"Updated memory: {memory}")







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
from aggregation_handler import detect_aggregation, build_aggregation_query, is_percentage_prompt

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
business_terms_path = "data/business_mapping.json"
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

    # Handle percentage queries
    percentage_match = re.search(r"what is the percentage of ([\w\s]+?)(?: applications)?(?:\s+over\s+([\w\s]+?)(?: applications)?)?", prompt_lower)
    if percentage_match or "percentage" in prompt_lower or is_percentage_prompt(prompt):
        try:
            numerator_terms = percentage_match.group(1).strip().split() if percentage_match else [term for term in business_terms if term in prompt_lower]
            denominator_term = percentage_match.group(2).strip() if percentage_match and percentage_match.group(2) else None
            percentage_filters = []
            for term in numerator_terms:
                rule = business_terms.get(term)
                if rule and rule["table"].lower() == table_name:
                    col = rule["column"].upper()
                    val = str(rule["value"]).upper() if isinstance(rule["value"], (bool, int)) and rule["value"] in [0, 1] else f"'{rule['value']}'"
                    percentage_filters.append(f"{col} = {val}")
            if percentage_filters:
                percentage_condition = " AND ".join(percentage_filters)
            else:
                percentage_condition = " AND ".join(all_filters) if all_filters else "TRUE"
            denominator_condition = None
            if denominator_term:
                rule = business_terms.get(denominator_term)
                if rule and rule["table"].lower() == table_name:
                    col = rule["column"].upper()
                    val = str(rule["value"]).upper() if isinstance(rule["value"], (bool, int)) and rule["value"] in [0, 1] else f"'{rule['value']}'"
                    denominator_condition = f"{col} = {val}"
            where_clause = f" WHERE {' AND '.join(all_filters)}" if all_filters else ""
            numerator = f"COUNT(CASE WHEN {percentage_condition} THEN 1 END)"
            denominator = f"COUNT(CASE WHEN {denominator_condition} THEN 1 END)" if denominator_condition else "NULLIF(COUNT(*), 0)"
            sql = f"SELECT ROUND(100.0 * {numerator} / {denominator}, 2) AS percentage_result FROM {table_name}{where_clause}"
            limit = extract_limit_from_prompt(prompt)
            sql = re.sub(r"\bLIMIT\s+\d+", "", sql, re.IGNORECASE).strip() + f" LIMIT {limit}"
            logger.info(f"Generated follow-up percentage SQL: '{sql}'")
            add_to_memory(memory_context, prompt, sql, table_name, schema, updated_filters)
            return sql
        except Exception as e:
            logger.error(f"Failed to build percentage query: {e}")
            return None

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