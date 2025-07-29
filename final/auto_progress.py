import re
import json
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
        rf'(?:{"|".join(progress_keywords)})\s*(?:in)?\s*(?:q[1-4])?',  # Matches "progress in Q2", "progress", "Q2 progress"
        rf'what\s*(?:is|are)\s*(?:a|the)?\s*(?:{"|".join(progress_keywords)})',  # Matches "what is progress", "what is the progress"
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
    today = datetime.now()
    current_year = today.year
    current_quarter = ((today.month - 1) // 3) + 1

    # Extract quarter and year from prompt
    quarter_match = re.search(r'q([1-4])', prompt.lower())
    year_match = re.search(r'(\d{4})', prompt.lower())
    
    if quarter_match:
        quarter = int(quarter_match.group(1))
    else:
        quarter = current_quarter

    year = int(year_match.group(1)) if year_match else current_year

    start_month = (quarter - 1) * 3 + 1
    from_dt = datetime(year, start_month, 1).strftime("%Y-%m-%d")
    to_dt = (datetime(year, start_month + 2, 1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    to_dt = to_dt.strftime("%Y-%m-%d")
    
    # For Q3, limit to current date if it includes future dates
    if quarter == current_quarter and datetime.strptime(to_dt, "%Y-%m-%d") > today:
        to_dt = today.strftime("%Y-%m-%d")
        logger.info(f"Adjusted Q{quarter} {year} end date to current date: {to_dt}")

    logger.info(f"Selected quarter Q{quarter} {year}: {from_dt} to {to_dt}")

    months = []
    current = datetime.strptime(from_dt, "%Y-%m-%d")
    end = datetime.strptime(to_dt, "%Y-%m-%d")
    while current <= end:
        if current.day == 1:
            months.append(current.strftime("%Y-%m"))
        current += timedelta(days=1)
    return from_dt, to_dt, months[:3]  # Limit to 3 months

def build_progress_query(prompt, schema_metadata, business_terms):
    """Build a SQL query for progress metrics and return with metadata."""
    is_progress, _ = detect_progress_request(prompt)
    if not is_progress:
        return None

    from_dt, to_dt, months = get_quarter_range(prompt)
    queries = []

    # Prioritize afnc_dsi_orgn_acct_dy table
    target_table = 'afnc_dsi_orgn_acct_dy'
    if target_table not in schema_metadata:
        logger.warning(f"Target table '{target_table}' not found in schema_metadata. Available tables: {list(schema_metadata.keys())}")
        # Fallback to first table with boolean columns
        for table_name, metadata in schema_metadata.items():
            columns = metadata.get("columns", {})
            if any(meta.get("type") == "boolean" for col, meta in columns.items()):
                target_table = table_name
                break
        if not target_table:
            logger.error(f"No table with boolean columns found in schema_metadata")
            return {
                "sql": None,
                "table": target_table,
                "date_range": {"from": from_dt, "to": to_dt},
                "error": f"No table with boolean columns found in schema_metadata"
            }

    metadata = schema_metadata.get(target_table, {})
    columns = metadata.get("columns", {})
    date_col = next((col for col, meta in columns.items() if meta.get("type") in ["date", "timestamp"]), None)
    if not date_col:
        logger.warning(f"No date or timestamp column found in '{target_table}' table metadata.")
        return {
            "sql": None,
            "table": target_table,
            "date_range": {"from": from_dt, "to": to_dt},
            "error": f"No date or timestamp column found in '{target_table}' table metadata"
        }

    # Use business terms to identify approval and booking flags
    approval_flag = None
    booking_flag = None
    for term, rule in business_terms.items():
        if rule["table"].upper() == target_table.upper():
            col = rule["column"].upper()
            if term.lower() in ["approved", "approval"]:
                approval_flag = col
            elif term.lower() in ["booked", "booking"]:
                booking_flag = col
    if not approval_flag:
        approval_flag = next((col for col, meta in columns.items() if meta.get("type") == "boolean"), None)
    if not booking_flag:
        booking_flag = next((col for col, meta in columns.items() if meta.get("type") == "boolean" and col != approval_flag), approval_flag)
    if not approval_flag or not booking_flag:
        logger.warning(f"Insufficient boolean columns for approval/booking flags in '{target_table}'.")
        return {
            "sql": None,
            "table": target_table,
            "date_range": {"from": from_dt, "to": to_dt},
            "error": f"Insufficient boolean columns for approval/booking flags in '{target_table}'"
        }

    # Use available numeric column for amounts
    amount_col = next((col for col, meta in columns.items() if meta.get("type") == "numeric"), None)
    if not amount_col:
        logger.warning(f"No numeric column found in '{target_table}' table for amount categories.")
        return {
            "sql": None,
            "table": target_table,
            "date_range": {"from": from_dt, "to": to_dt},
            "error": f"No numeric column found in '{target_table}' table for amount categories"
        }

    # Build select clauses
    select_clauses_base = ["? AS Month"]
    select_clauses_base.append(f"COUNT(*) AS Total_Apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag} = '1' THEN 1 END) AS approved_apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {booking_flag} = '1' THEN 1 END) AS booked_apps")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag} = '1' AND {booking_flag} = '1' THEN 1 END) AS approved_and_booked")
    select_clauses_base.append(f"COUNT(CASE WHEN {approval_flag} = '1' AND {booking_flag} = '0' THEN 1 END) AS approved_not_booked")
    select_clauses_base.append(f"SUM(CASE WHEN {amount_col} IS NOT NULL THEN {amount_col} ELSE 0 END) AS total_amount")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col} < 10000 THEN 1 END) AS under_10k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col} < 20000 THEN 1 END) AS under_20k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col} < 30000 THEN 1 END) AS under_30k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col} < 40000 THEN 1 END) AS under_40k")
    select_clauses_base.append(f"COUNT(CASE WHEN {amount_col} >= 50000 THEN 1 END) AS above_50k")

    # Build query for each month
    queries = []
    zero_results = []
    for month in months:
        month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%Y-%m-%d")
        month_end = (datetime.strptime(f"{month}-01", "%Y-%m-%d") + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        month_end = min(month_end, datetime.now()).strftime("%Y-%m-%d")  # Cap at current date

        select_clauses = select_clauses_base.copy()
        select_clauses[0] = f"'{month}' AS Month"
        where_clause = f"WHERE {date_col} BETWEEN '{month_start}' AND '{month_end}'"

        query = f"SELECT {', '.join(select_clauses)} FROM {target_table} {where_clause}"
        queries.append(query)

        # Prepare zero-filled result for this month
        zero_results.append({
            "Month": month,
            "Total_Apps": 0,
            "approved_apps": 0,
            "booked_apps": 0,
            "approved_and_booked": 0,
            "approved_not_booked": 0,
            "total_amount": 0,
            "under_10k": 0,
            "under_20k": 0,
            "under_30k": 0,
            "under_40k": 0,
            "above_50k": 0
        })

    return {
        "sql": " UNION ALL ".join(queries) if queries else None,
        "table": target_table,
        "date_range": {"from": from_dt, "to": to_dt},
        "zero_results": zero_results  # Default results if no data
    }