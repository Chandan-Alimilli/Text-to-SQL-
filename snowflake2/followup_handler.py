import re
import logging
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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MEMORY = 5

# Enhanced follow-up trigger phrases
FOLLOWUP_KEYWORDS = [
    "show from above", "those", "them", "again", "only those", "just those",
    "from earlier", "refine", "filter those", "in context", "previous data",
    "based on above", "give me those", "those entries", "those applications",
    "can I see", "again please", "from previous result", "follow up",
    "carry over", "now show", "more on those", "apply to those",
    "same records", "previous ones", "those results", "revisit those",
    "filter previous", "from that", "keep those", "show again",
    "based on last", "same ones", "narrow down those"
]

def is_follow_up_prompt(prompt):
    """Check if the prompt is a follow-up query."""
    prompt_lower = normalize_text(prompt).lower()
    result = any(key in prompt_lower for key in FOLLOWUP_KEYWORDS)
    logger.debug(f"Follow-up prompt detected: {result} for prompt: {prompt}")
    return result

def get_followup_query(prompt, memory_context):
    """Generate SQL query for follow-up prompt based on previous context."""
    prompt_lower = prompt.lower()
    prompt_norm = normalize_text(prompt)
    if not is_follow_up_prompt(prompt_lower) or not memory_context:
        logger.warning("No follow-up detected or no memory context available")
        return None

    # Iterate over recent memory (last MAX_MEMORY entries)
    for mem in reversed(memory_context[-MAX_MEMORY:]):
        last_prompt = mem.get("prompt", "").lower()
        last_sql = mem.get("sql", "")
        logger.debug(f"Processing memory: prompt={last_prompt}, sql={last_sql}")

        # Extract table name from previous SQL
        table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
        table = table_match.group(1).upper() if table_match else None
        if not table or table not in schema_metadata:
            logger.warning(f"Invalid table {table} or not in schema_metadata")
            continue

        columns = schema_metadata[table]["columns"]

        # Detect if the follow-up is an aggregation query
        try:
            agg_func, agg_col = detect_aggregation(prompt, columns)
            logger.debug(f"Detected aggregation: {agg_func} on column {agg_col}")
        except Exception as e:
            agg_func, agg_col = None, None
            logger.debug(f"No aggregation detected: {e}")

        # Extract previous WHERE clause
        where_match = re.search(r"\bWHERE\b(.+?)(?:LIMIT|ORDER|$)", last_sql, re.IGNORECASE)
        prev_where_clause = where_match.group(1).strip() if where_match else ""
        logger.debug(f"Previous WHERE clause: {prev_where_clause}")

        # Extract new filters from current prompt
        new_filters = []
        new_filters += extract_direct_column_filters(prompt, columns)
        new_filters += extract_comparative_filters(prompt, columns)

        # Handle date range (consistent with mapper_utils)
        from_dt, to_dt = parse_date_range_from_prompt(prompt)
        date_cols = [col for col in columns if isinstance(columns[col], dict) and columns[col].get("type") in ("date", "timestamp")]
        if from_dt and to_dt and date_cols:
            date_col = date_cols[0].upper()
            new_filters.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            logger.debug(f"Added date filter: {date_col} BETWEEN '{from_dt}' AND '{to_dt}'")

        # Combine filters
        all_filters = []
        if prev_where_clause:
            all_filters.append(f"({prev_where_clause})")
        if new_filters:
            all_filters.append(" AND ".join(new_filters))

        # Handle aggregation follow-up
        if agg_func:
            try:
                # Build aggregation query with combined filters
                where_clause = " WHERE " + " AND ".join(all_filters) if all_filters else ""
                sql = build_aggregation_query(agg_func, agg_col, table, prompt, columns)
                # Replace the default WHERE clause with combined filters
                if where_clause:
                    sql = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, sql, flags=re.IGNORECASE)
                    if "LIMIT" not in sql.upper():
                        limit = extract_limit_from_prompt(prompt)
                        sql += f" LIMIT {limit}"
                logger.info(f"Generated follow-up aggregation SQL: {sql}")
                return sql
            except Exception as e:
                logger.error(f"Failed to build aggregation query: {e}")
                continue

        # Default to SELECT query for non-aggregation follow-ups
        all_cols = ", ".join(columns.keys())
        new_sql = f"SELECT {all_cols} FROM {table}"

        if all_filters:
            new_sql += " WHERE " + " AND ".join(all_filters)

        # Add LIMIT
        limit = extract_limit_from_prompt(prompt)
        if limit:
            new_sql += f" LIMIT {limit}"
        elif "LIMIT" in last_sql.upper():
            last_limit = re.search(r"LIMIT\s+\d+", last_sql, re.IGNORECASE)
            if last_limit:
                new_sql += f" {last_limit.group()}"
        logger.info(f"Generated follow-up SQL: {new_sql}")
        return new_sql

    logger.warning("No valid follow-up SQL generated from memory context")
    return None

def add_to_memory(memory, prompt, sql):
    """Append prompt and SQL to memory context."""
    memory.append({
        "prompt": prompt,
        "sql": sql
    })
    if len(memory) > MAX_MEMORY:
        memory.pop(0)
    logger.debug(f"Updated memory: {memory}")




