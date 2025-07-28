import re
from datetime import datetime, timedelta
import logging
from mapper_utils import parse_date_range_from_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_progress_request(prompt, rag_tables=None):
    """Detect if the prompt requests progress or performance."""
    prompt_lower = prompt.lower()
    progress_keywords = ['progress', 'performance']
    progress_patterns = [
        rf'what is a\s+(?:{"|".join(progress_keywords)})',
        rf'what is the\s+(?:{"|".join(progress_keywords)})'
    ]
    matched_pattern = None
    for pattern in progress_patterns:
        if re.search(pattern, prompt_lower):
            matched_pattern = pattern
            break
    if matched_pattern:
        logger.debug(f"Detected progress request with pattern: {matched_pattern}")
        return True, None  # Table will be determined from schema_metadata
    logger.debug(f"No progress request detected. Checked patterns: {progress_patterns}")
    return False, None

def get_quarter_range(prompt):
    """Get the start and end dates of the quarter, and derive the three months."""
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    if not from_dt or not to_dt:
        today = datetime.now()
        current_month = today.month
        quarter = ((current_month - 1) // 3) + 1
        year = today.year if quarter <= 3 else today.year - 1
        start_month = (quarter - 1) * 3 + 1
        from_dt = datetime(year, start_month, 1).strftime("%Y-%m-%d")
        to_dt = (datetime(year, start_month + 2, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        to_dt = to_dt.strftime("%Y-%m-%d")
        logger.info(f"Defaulted to current quarter {quarter} {year}: {from_dt} to {to_dt}")
    months = []
    current = datetime.strptime(from_dt, "%Y-%m-%d")
    end = datetime.strptime(to_dt, "%Y-%m-%d")
    while current <= end:
        if current.day == 1:
            months.append(current.strftime("%Y-%m"))
        current += timedelta(days=1)
    return from_dt, to_dt, months[:3]  # Limit to 3 months

def build_progress_query(prompt, schema_metadata, business_terms):
    """Build a SQL query for progress metrics using available schema_metadata."""
    is_progress, _ = detect_progress_request(prompt)
    if not is_progress:
        return None

    from_dt, to_dt, months = get_quarter_range(prompt)
    queries = []

    # Use the first table with boolean columns for progress metrics
    target_table = None
    for table_name, metadata in schema_metadata.items():
        columns = metadata.get("columns", {})
        if any(meta.get("type") == "boolean" for col, meta in columns.items()):
            target_table = table_name
            break
    if not target_table:
        logger.warning(f"No table with boolean columns found in schema_metadata. Available tables: {list(schema_metadata.keys())}")
        return None

    metadata = schema_metadata.get(target_table, {})
    columns = metadata.get("columns", {})
    date_col = next((col for col, meta in columns.items() if meta.get("type") in ["date", "timestamp"]), None)
    if not date_col:
        logger.warning(f"No date or timestamp column found in '{target_table}' table metadata.")
        return None

    # Use available boolean columns for flags
    flags = {col: meta for col, meta in columns.items() if meta.get("type") == "boolean"}
    if not flags:
        logger.warning(f"No boolean columns found in '{target_table}' table.")
        return None
    approval_flag = next(iter(flags))  # Use first boolean column as approval proxy
    booking_flag = next((col for col in flags if col != approval_flag), approval_flag)  # Use second if available, else same

    # Use available numeric column for amounts
    amount_col = next((col for col, meta in columns.items() if meta.get("type") == "numeric"), None)
    if not amount_col:
        logger.warning(f"No numeric column found in '{target_table}' table for amount categories.")
        return None

    # Build select clauses
    select_clauses_base = ["'?' AS Month"]
    select_clauses_base.append(f"COUNT(*) AS Total_Apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag.upper()} = '1' THEN 1 END) AS approved_apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {booking_flag.upper()} = '1' THEN 1 END) AS booked_apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag.upper()} = '1' AND {booking_flag.upper()} = '1' THEN 1 END) AS approved_and_booked")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag.upper()} = '1' AND {booking_flag.upper()} = '0' THEN 1 END) AS approved_not_booked")
    select_clauses_base.append(f"SUM(CASE WHEN {amount_col.upper()} IS NOT NULL THEN {amount_col.upper()} ELSE 0 END) AS total_amount")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col.upper()} < 10000 THEN 1 END) AS under_10k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col.upper()} < 20000 THEN 1 END) AS under_20k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col.upper()} < 30000 THEN 1 END) AS under_30k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col.upper()} < 40000 THEN 1 END) AS under_40k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col.upper()} >= 50000 THEN 1 END) AS above_50k")

    # Build query for each month
    for month in months:
        month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%Y-%m-%d")
        month_end = (datetime.strptime(f"{month}-01", "%Y-%m-%d") + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        month_end = month_end.strftime("%Y-%m-%d")

        select_clauses = select_clauses_base.copy()
        select_clauses[0] = f"'{month}' AS Month"
        where_clause = f"WHERE {date_col.upper()} BETWEEN '{month_start}' AND '{month_end}'"

        query = f"SELECT {', '.join(select_clauses)} FROM {target_table.upper()} {where_clause}"
        queries.append(query)

    return " UNION ALL ".join(queries) if queries else None




























