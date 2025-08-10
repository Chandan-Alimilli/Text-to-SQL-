
# import re
# import json
# from datetime import datetime, timedelta
# import logging
# from mapper_utils import parse_date_range_from_prompt

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def detect_progress_request(prompt, rag_tables=None):
#     """Detect if the prompt requests progress or performance and identify the target table."""
#     prompt_lower = prompt.lower()
#     progress_keywords = ['progress', 'performance', 'metrics']
#     table_keywords = {
#         'closing fee table': 'auto_fnce_orgn_refn_clse_fee',
#         'eligible': 'auto_fnce_orgn_refn_elg',
#         'closing': 'auto_fnce_orgn_refn_clse',
#         'refinance accounts table': 'afnc_dsi_orgn_acct_dy',
#         'approval table': 'afnc_dsi_orgn_acct_dy',
#         'accounts table': 'afnc_dsi_orgn_acct_dy'
#     }
#     progress_patterns = [
#         rf'(?:{"|".join(progress_keywords)})\s*(?:in)?\s*(?:q[1-4]|\w+ \d{4})?\s*(?:{"|".join(table_keywords.keys())})?',
#         rf'what\s*(?:is|are)\s*(?:a|the)?\s*(?:{"|".join(progress_keywords)})',
#     ]
#     matched_pattern = None
#     target_table = None
#     for pattern in progress_patterns:
#         match = re.search(pattern, prompt_lower)
#         if match:
#             matched_pattern = pattern
#             # Extract table if mentioned
#             for table_phrase, table_name in table_keywords.items():
#                 if table_phrase in prompt_lower:
#                     target_table = table_name
#             break
#     if matched_pattern:
#         logger.debug(f"Detected progress request with pattern: {matched_pattern}, target_table: {target_table}")
#         return True, target_table
#     logger.debug(f"No progress request detected. Checked patterns: {progress_patterns}")
#     return False, None

# def get_period_range(prompt):
#     """Get the start and end dates of the period using mapper_utils parse_date_range_from_prompt."""
#     from_dt, to_dt = parse_date_range_from_prompt(prompt)
#     if not from_dt or not to_dt:
#         # Default to full year 2025 for testing
#         from_dt = "2025-01-01"
#         to_dt = "2025-12-31"
#         logger.info(f"Defaulting to full year 2025 for testing: {from_dt} to {to_dt}")
#     else:
#         logger.info(f"Parsed date range from prompt: {from_dt} to {to_dt}")
    
#     months = []
#     current = datetime.strptime(from_dt, "%Y-%m-%d")
#     end = datetime.strptime(to_dt, "%Y-%m-%d")
#     while current <= end:
#         if current.day == 1:
#             months.append(current.strftime("%Y-%m"))
#         current += timedelta(days=1)
#     return from_dt, to_dt, months

# def build_progress_query(prompt, schema_metadata, business_terms):
#     """Build a SQL query for progress metrics and return with metadata."""
#     is_progress, target_table = detect_progress_request(prompt)
#     if not is_progress:
#         return None

#     from_dt, to_dt, months = get_period_range(prompt)
#     queries = []

#     # Define table-specific metrics and a unified set of all metrics
#     table_metrics = {
#         "afnc_dsi_orgn_acct_dy": {
#             "date_col": "APPL_INIT_DT",
#             "metrics": [
#                 ("COUNT(*)", "total_applications"),
#                 ("COUNT(CASE WHEN APPL_APRV_IN = 1 THEN 1 END)", "approved_applications"),
#                 ("COUNT(CASE WHEN BK_IN = 1 THEN 1 END)", "booked_applications"),
#                 ("SUM(APRV_LOAN_AM)", "total_loan_amount"),
#                 ("SUM(APRV_LOAN_PYMT_AM)", "total_loan_payment"),
#                 ("SUM(APRV_PYMT_AM)", "total_payment_amount"),
#                 ("NULL", "inProgress_tasks"),
#                 ("NULL", "completed_tasks"),
#                 ("NULL", "failed_tasks"),
#                 ("NULL", "notStarted_tasks"),
#                 ("NULL", "moreInfomationNeeded_tasks"),
#                 ("NULL", "total_vehicle_fees"),
#                 ("NULL", "total_loan_payoff"),
#                 ("NULL", "total_additional_fees"),
#                 ("NULL", "eligible_applications"),
#                 ("NULL", "ineligible_applications"),
#                 ("NULL", "state_allowed")
#             ]
#         },
#         "auto_fnce_orgn_refn_clse": {
#             "date_col": "SNPST_DT",
#             "metrics": [
#                 ("COUNT(*)", "total_tasks"),
#                 ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'inProgress' THEN 1 END)", "inProgress_tasks"),
#                 ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'completed' THEN 1 END)", "completed_tasks"),
#                 ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'failed' THEN 1 END)", "failed_tasks"),
#                 ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'notStarted' THEN 1 END)", "notStarted_tasks"),
#                 ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'moreInfomationNeeded' THEN 1 END)", "moreInfomationNeeded_tasks"),
#                 ("NULL", "total_applications"),
#                 ("NULL", "approved_applications"),
#                 ("NULL", "booked_applications"),
#                 ("NULL", "total_loan_amount"),
#                 ("NULL", "total_loan_payment"),
#                 ("NULL", "total_payment_amount"),
#                 ("NULL", "total_vehicle_fees"),
#                 ("NULL", "total_loan_payoff"),
#                 ("NULL", "total_additional_fees"),
#                 ("NULL", "eligible_applications"),
#                 ("NULL", "ineligible_applications"),
#                 ("NULL", "state_allowed")
#             ]
#         },
#         "auto_fnce_orgn_refn_clse_fee": {
#             "date_col": "SNPST_DT",
#             "metrics": [
#                 ("COUNT(DISTINCT APPL_NB)", "total_applications"),
#                 ("SUM(VHCL_FEE_AM)", "total_vehicle_fees"),
#                 ("SUM(ORGN_LOAN_PYF_AM)", "total_loan_payoff"),
#                 ("SUM(ADDL_FEE_AM)", "total_additional_fees"),
#                 ("NULL", "inProgress_tasks"),
#                 ("NULL", "completed_tasks"),
#                 ("NULL", "failed_tasks"),
#                 ("NULL", "notStarted_tasks"),
#                 ("NULL", "moreInfomationNeeded_tasks"),
#                 ("NULL", "approved_applications"),
#                 ("NULL", "booked_applications"),
#                 ("NULL", "total_loan_amount"),
#                 ("NULL", "total_loan_payment"),
#                 ("NULL", "total_payment_amount"),
#                 ("NULL", "eligible_applications"),
#                 ("NULL", "ineligible_applications"),
#                 ("NULL", "state_allowed")
#             ]
#         },
#         "auto_fnce_orgn_refn_elg": {
#             "date_col": "SNPST_DT",
#             "metrics": [
#                 ("COUNT(*)", "total_applications"),
#                 ("COUNT(CASE WHEN REFN_EL_IN = 1 THEN 1 END)", "eligible_applications"),
#                 ("COUNT(CASE WHEN REFN_EL_IN = 0 THEN 1 END)", "ineligible_applications"),
#                 ("COUNT(CASE WHEN STATE_ALOW_IN = 1 THEN 1 END)", "state_allowed"),
#                 ("NULL", "inProgress_tasks"),
#                 ("NULL", "completed_tasks"),
#                 ("NULL", "failed_tasks"),
#                 ("NULL", "notStarted_tasks"),
#                 ("NULL", "moreInfomationNeeded_tasks"),
#                 ("NULL", "approved_applications"),
#                 ("NULL", "booked_applications"),
#                 ("NULL", "total_loan_amount"),
#                 ("NULL", "total_loan_payment"),
#                 ("NULL", "total_payment_amount"),
#                 ("NULL", "total_vehicle_fees"),
#                 ("NULL", "total_loan_payoff"),
#                 ("NULL", "total_additional_fees"),
#                 ("NULL", "unused_placeholder")  # Ensures 18 columns
#             ]
#         }
#     }

#     # If target_table is specified, use it; otherwise, aggregate across all tables
#     tables_to_process = [target_table] if target_table else table_metrics.keys()

#     # Preliminary data check (simulated, actual execution needed)
#     for table in tables_to_process:
#         date_col = table_metrics[table]["date_col"]
#         check_query = f"SELECT COUNT(*) FROM {table} WHERE {date_col} IS NOT NULL"
#         logger.info(f"Data check for {table}: Query {check_query} (Note: Actual count requires manual execution)")
#         # Placeholder: Actual count would need to be executed against the database

#     # Build queries for each table
#     all_zero_results = []
#     for table in tables_to_process:
#         if table not in schema_metadata or table not in table_metrics:
#             logger.warning(f"Table {table} not found in schema_metadata or metrics definition")
#             continue

#         metadata = schema_metadata.get(table, {})
#         columns = metadata.get("columns", {})
#         date_col = table_metrics[table]["date_col"]
#         metrics = table_metrics[table]["metrics"]

#         # Build select clauses
#         select_clause = ["'?' AS month"]  # Placeholder for month
#         for metric_expr, metric_alias in metrics:
#             select_clause.append(f"{metric_expr} AS {metric_alias}")
#         logger.debug(f"Base select clause for {table}: {', '.join(select_clause)} (columns: {len(select_clause)})")

#         # Build query for each month
#         table_queries = []
#         zero_results = []
#         for month in months:
#             month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%Y-%m-%d")
#             month_end = (datetime.strptime(f"{month}-01", "%Y-%m-%d") + timedelta(days=31)).replace(day=1) - timedelta(days=1)
#             month_end = min(month_end, datetime.now()).strftime("%Y-%m-%d")

#             # Replace placeholder with actual month
#             query_select = [f"'{month}' AS month"] + select_clause[1:]  # Exclude the placeholder, add metrics
#             where_clause = f"WHERE {date_col} BETWEEN '{month_start}' AND '{month_end}'"
#             query = f"SELECT {', '.join(query_select)} FROM {table} {where_clause}"
#             table_queries.append(query)

#             # Prepare zero-filled result for this month
#             zero_result = {"month": month, "table": table}
#             for _, metric_alias in metrics:
#                 zero_result[metric_alias] = 0
#             zero_results.append(zero_result)

#         queries.extend(table_queries)
#         all_zero_results.extend(zero_results)

#     final_sql = " UNION ALL ".join(queries) if queries else None
#     if final_sql:
#         # Validate column count in final SQL
#         import re
#         column_count = len(re.findall(r'AS\s+\w+', final_sql.split('UNION ALL')[0]))
#         logger.debug(f"Final SQL column count: {column_count}")
#         logger.info(f"Executing query for tables: {', '.join(tables_to_process)} with date range {from_dt} to {to_dt}")
#     return {
#         "sql": final_sql,
#         "table": target_table or "all_tables",
#         "date_range": {"from": from_dt, "to": to_dt},
#         "zero_results": all_zero_results
#     }


















import re
import json
from datetime import datetime, timedelta
import logging
from mapper_utils import parse_date_range_from_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_progress_request(prompt, rag_tables=None):
    """Detect if the prompt requests progress or performance and identify the target table."""
    prompt_lower = prompt.lower()
    progress_keywords = ['progress', 'performance', 'metrics']
    table_keywords = {
        'closing fee table': 'auto_fnce_orgn_refn_clse_fee',
        'closing fee': 'auto_fnce_orgn_refn_clse_fee',
        'eligible': 'auto_fnce_orgn_refn_elg',
        'closing': 'auto_fnce_orgn_refn_clse',
        'refinance accounts table': 'afnc_dsi_orgn_acct_dy',
        'approval table': 'afnc_dsi_orgn_acct_dy',
        'accounts table': 'afnc_dsi_orgn_acct_dy'
    }
    progress_patterns = [
        rf'(?:{"|".join(progress_keywords)})\s*(?:in)?\s*(?:q[1-4]|\w+ \d{4})?\s*(?:{"|".join(table_keywords.keys())})?',
        rf'what\s*(?:is|are)\s*(?:a|the)?\s*(?:{"|".join(progress_keywords)})',
    ]
    matched_pattern = None
    target_table = None
    for pattern in progress_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            matched_pattern = pattern
            # Extract table if mentioned
            for table_phrase, table_name in table_keywords.items():
                if table_phrase in prompt_lower:
                    target_table = table_name
            break
    if matched_pattern:
        logger.debug(f"Detected progress request with pattern: {matched_pattern}, target_table: {target_table}")
        return True, target_table
    logger.debug(f"No progress request detected. Checked patterns: {progress_patterns}")
    return False, None

def get_period_range(prompt):
    """Get the start and end dates of the period using mapper_utils parse_date_range_from_prompt."""
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    if not from_dt or not to_dt:
        # Default to a recent year (2024) to match potential data availability
        from_dt = "2024-01-01"
        to_dt = "2024-12-31"
        logger.info(f"Defaulting to full year 2024 for testing: {from_dt} to {to_dt}")
    else:
        logger.info(f"Parsed date range from prompt: {from_dt} to {to_dt}")
    
    months = []
    current = datetime.strptime(from_dt, "%Y-%m-%d")
    end = datetime.strptime(to_dt, "%Y-%m-%d")
    while current <= end:
        if current.day == 1:
            months.append(current.strftime("%Y-%m"))
        current += timedelta(days=1)
    return from_dt, to_dt, months

def build_progress_query(prompt, schema_metadata, business_terms):
    """Build a SQL query for progress metrics and return with metadata."""
    is_progress, target_table = detect_progress_request(prompt)
    if not is_progress:
        return None

    from_dt, to_dt, months = get_period_range(prompt)
    queries = []

    # Define table-specific metrics and a unified set of all metrics
    table_metrics = {
        "afnc_dsi_orgn_acct_dy": {
            "date_col": "APPL_INIT_DT",
            "metrics": [
                ("COUNT(*)", "total_applications"),
                ("COUNT(CASE WHEN APPL_APRV_IN = 1 THEN 1 END)", "approved_applications"),
                ("COUNT(CASE WHEN BK_IN = 1 THEN 1 END)", "booked_applications"),
                ("SUM(APRV_LOAN_AM)", "total_loan_amount"),
                ("SUM(APRV_LOAN_PYMT_AM)", "total_loan_payment"),
                ("SUM(APRV_PYMT_AM)", "total_payment_amount"),
                ("NULL", "inProgress_tasks"),
                ("NULL", "completed_tasks"),
                ("NULL", "failed_tasks"),
                ("NULL", "notStarted_tasks"),
                ("NULL", "moreInfomationNeeded_tasks"),
                ("NULL", "total_vehicle_fees"),
                ("NULL", "total_loan_payoff"),
                ("NULL", "total_additional_fees"),
                ("NULL", "eligible_applications"),
                ("NULL", "ineligible_applications"),
                ("NULL", "state_allowed")
            ]
        },
        "auto_fnce_orgn_refn_clse": {
            "date_col": "SNPST_DT",
            "metrics": [
                ("COUNT(*)", "total_tasks"),
                ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'inProgress' THEN 1 END)", "inProgress_tasks"),
                ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'completed' THEN 1 END)", "completed_tasks"),
                ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'failed' THEN 1 END)", "failed_tasks"),
                ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'notStarted' THEN 1 END)", "notStarted_tasks"),
                ("COUNT(CASE WHEN CLSE_TASK_STG_STS_TX = 'moreInfomationNeeded' THEN 1 END)", "moreInfomationNeeded_tasks"),
                ("NULL", "total_applications"),
                ("NULL", "approved_applications"),
                ("NULL", "booked_applications"),
                ("NULL", "total_loan_amount"),
                ("NULL", "total_loan_payment"),
                ("NULL", "total_payment_amount"),
                ("NULL", "total_vehicle_fees"),
                ("NULL", "total_loan_payoff"),
                ("NULL", "total_additional_fees"),
                ("NULL", "eligible_applications"),
                ("NULL", "ineligible_applications"),
                ("NULL", "state_allowed")
            ]
        },
        "auto_fnce_orgn_refn_clse_fee": {
            "date_col": "SNPST_DT",
            "metrics": [
                ("COUNT(DISTINCT APPL_NB)", "total_applications"),
                ("SUM(VHCL_FEE_AM)", "total_vehicle_fees"),
                ("SUM(ORGN_LOAN_PYF_AM)", "total_loan_payoff"),
                ("SUM(ADDL_FEE_AM)", "total_additional_fees"),
                ("NULL", "inProgress_tasks"),
                ("NULL", "completed_tasks"),
                ("NULL", "failed_tasks"),
                ("NULL", "notStarted_tasks"),
                ("NULL", "moreInfomationNeeded_tasks"),
                ("NULL", "approved_applications"),
                ("NULL", "booked_applications"),
                ("NULL", "total_loan_amount"),
                ("NULL", "total_loan_payment"),
                ("NULL", "total_payment_amount"),
                ("NULL", "eligible_applications"),
                ("NULL", "ineligible_applications"),
                ("NULL", "state_allowed")
            ]
        },
        "auto_fnce_orgn_refn_elg": {
            "date_col": "SNPST_DT",
            "metrics": [
                ("COUNT(*)", "total_applications"),
                ("COUNT(CASE WHEN REFN_EL_IN = 1 THEN 1 END)", "eligible_applications"),
                ("COUNT(CASE WHEN REFN_EL_IN = 0 THEN 1 END)", "ineligible_applications"),
                ("COUNT(CASE WHEN STATE_ALOW_IN = 1 THEN 1 END)", "state_allowed"),
                ("NULL", "inProgress_tasks"),
                ("NULL", "completed_tasks"),
                ("NULL", "failed_tasks"),
                ("NULL", "notStarted_tasks"),
                ("NULL", "moreInfomationNeeded_tasks"),
                ("NULL", "approved_applications"),
                ("NULL", "booked_applications"),
                ("NULL", "total_loan_amount"),
                ("NULL", "total_loan_payment"),
                ("NULL", "total_payment_amount"),
                ("NULL", "total_vehicle_fees"),
                ("NULL", "total_loan_payoff"),
                ("NULL", "total_additional_fees"),
                ("NULL", "unused_placeholder")  # Ensures 18 columns
            ]
        }
    }

    # If target_table is specified, use it; otherwise, aggregate across all tables
    tables_to_process = [target_table] if target_table else table_metrics.keys()

    # Preliminary data check
    for table in tables_to_process:
        if table in table_metrics:
            date_col = table_metrics[table]["date_col"]
            check_query = f"SELECT COUNT(*) FROM {table} WHERE {date_col} IS NOT NULL"
            logger.info(f"Data check for {table}: Query {check_query} (Note: Actual execution required externally)")
            # Placeholder: Actual count would need to be executed against the database

    # Build queries for each table
    all_zero_results = []
    for table in tables_to_process:
        if table not in schema_metadata or table not in table_metrics:
            logger.warning(f"Table {table} not found in schema_metadata or metrics definition")
            continue

        metadata = schema_metadata.get(table, {})
        columns = metadata.get("columns", {})
        date_col = table_metrics[table]["date_col"]
        metrics = table_metrics[table]["metrics"]

        # Build select clauses
        select_clause = ["'?' AS month"]  # Placeholder for month
        for metric_expr, metric_alias in metrics:
            select_clause.append(f"{metric_expr} AS {metric_alias}")
        logger.debug(f"Base select clause for {table}: {', '.join(select_clause)} (columns: {len(select_clause)})")

        # Build query for each month
        table_queries = []
        zero_results = []
        for month in months:
            month_start = datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%Y-%m-%d")
            month_end = (datetime.strptime(f"{month}-01", "%Y-%m-%d") + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            month_end = min(month_end, datetime.strptime(to_dt, "%Y-%m-%d")).strftime("%Y-%m-%d")

            # Replace placeholder with actual month
            query_select = [f"'{month}' AS month"] + select_clause[1:]  # Exclude the placeholder, add metrics
            where_clause = f"WHERE {date_col} BETWEEN '{month_start}' AND '{month_end}'"
            query = f"SELECT {', '.join(query_select)} FROM {table} {where_clause}"
            table_queries.append(query)

            # Prepare zero-filled result for this month (placeholder, not final result)
            zero_result = {"month": month, "table": table}
            for _, metric_alias in metrics:
                zero_result[metric_alias] = 0
            zero_results.append(zero_result)

        queries.extend(table_queries)
        all_zero_results.extend(zero_results)

    final_sql = " UNION ALL ".join(queries) if queries else None
    if final_sql:
        # Validate column count in final SQL
        import re
        column_count = len(re.findall(r'AS\s+\w+', final_sql.split('UNION ALL')[0]))
        logger.debug(f"Final SQL column count: {column_count}")
        logger.info(f"Executing query for tables: {', '.join(tables_to_process)} with date range {from_dt} to {to_dt}")
    return {
        "sql": final_sql,
        "table": target_table or "all_tables",
        "date_range": {"from": from_dt, "to": to_dt},
        "zero_results": all_zero_results  # Marked as placeholder, actual results from query execution
    }