

# import re
# import json
# import logging
# from mapper_utils import normalize_text, extract_comparative_filters, extract_direct_column_filters, parse_date_range_from_prompt
# from rag_retriever import schema_metadata
# from aggregation_handler import is_percentage_prompt
# from db import execute_sql

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed tracing
# logger = logging.getLogger(__name__)

# # Load business term mappings
# try:
#     with open("data/business_mapping.json", "r") as f:
#         BUSINESS_TERMS = json.load(f)
# except Exception as e:
#     logger.error(f"Failed to load business_mapping.json: {e}")
#     raise

# def generate_summary_from_result(data, prompt, sql, table_name):
#     """Generate a human-readable summary of query results."""
#     if not data:
#         logger.warning("No records found for summary generation")
#         return "No records found for the given query."

#     try:
#         # Normalize prompt for processing
#         prompt_norm = normalize_text(prompt).lower()
#         logger.debug(f"Normalized prompt: {prompt_norm}")

#         # Extract table metadata
#         table_name_upper = table_name.upper()
#         table_metadata = schema_metadata.get(table_name_upper, {})
#         columns_meta = table_metadata.get("columns", {})
#         metadata_available = bool(columns_meta)
#         logger.debug(f"Metadata available for {table_name_upper}: {metadata_available}")

#         # Initialize summary
#         summary = []

#         # Extract conditions from prompt and SQL
#         conditions = []
#         business_terms = []
#         for key, rule in BUSINESS_TERMS.items():
#             if key in prompt_norm and rule["table"].lower() == table_name.lower():
#                 col = rule["column"]
#                 val = rule.get("value", "")
#                 if rule.get("not_null"):
#                     conditions.append(f"{col} is not null")
#                 elif rule.get("is_null"):
#                     conditions.append(f"{col} is null")
#                 else:
#                     val = str(val).upper() if isinstance(val, bool) else f"'{val}'"
#                     conditions.append(f"{col} = {val}")
#                 business_terms.append(key)
#         conditions += extract_comparative_filters(prompt, columns_meta)
#         conditions += extract_direct_column_filters(prompt, columns_meta)
#         logger.debug(f"Extracted conditions: {conditions}")
#         logger.debug(f"Business terms: {business_terms}")

#         # Date range
#         from_dt, to_dt = parse_date_range_from_prompt(prompt)
#         date_filter = ""
#         date_col = None
#         if from_dt and to_dt:
#             date_col = next((col for col, meta in columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
#             if date_col:
#                 date_filter = f"from {from_dt} to {to_dt}"
#                 conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
#             logger.debug(f"Date filter: {date_filter}")

#         # Non-aggregation query
#         record_count = len(data)
#         summary.append(f"You have {record_count} {'approved application' if 'approved' in business_terms else 'application'} records from {table_name_upper} {date_filter}")

#         # Add conditions
#         if business_terms or conditions:
#             summary.append("matching the following conditions:")
#             if business_terms:
#                 for term in business_terms:
#                     summary.append(f"- {term}")
#             for cond in conditions:
#                 cond_clean = re.sub(r"['\"]", "", cond).replace(" = ", " is ").replace(" > ", " exceeds ").replace("APRV_LOAN_PYMT_AM", "loan amount")
#                 summary.append(f"- {cond_clean}")
#         logger.debug(f"Conditions added to summary: {summary}")

#         # Numeric aggregations
#         numeric_cols = [col for col in data[0] if isinstance(data[0][col], (int, float)) and col in columns_meta]
#         if numeric_cols:
#             summary.append("\nKey numeric insights:")
#             for col in numeric_cols:
#                 col_vals = [row[col] for row in data if row[col] is not None]
#                 if col_vals:
#                     avg = sum(col_vals) / len(col_vals)
#                     total = sum(col_vals)
#                     min_val = min(col_vals)
#                     max_val = max(col_vals)
#                     col_desc = columns_meta.get(col, {}).get("desc", col.replace("_", " ").title()) if metadata_available else col.replace("_", " ").title()
#                     summary.append(f"- {col_desc}: Total = ${total:,.2f}, Average = ${avg:,.2f}, Min = ${min_val:,.2f}, Max = ${max_val:,.2f}")
#             logger.debug(f"Numeric aggregations for {numeric_cols}: Total={total}, Avg={avg}, Min={min_val}, Max={max_val}")

#         # Boolean aggregations
#         boolean_cols = [col for col in data[0] if isinstance(data[0][col], (int, bool)) and columns_meta.get(col, {}).get("type") == "boolean"]
#         if boolean_cols and metadata_available:
#             summary.append("\nKey boolean insights:")
#             for col in boolean_cols:
#                 true_count = sum(1 for row in data if row[col] in (1, True))
#                 percentage = (true_count / len(data)) * 100 if data else 0
#                 col_desc = columns_meta.get(col, {}).get("desc", col.replace("_", " ").title())
#                 summary.append(f"- {col_desc}: {percentage:.2f}% of records are true ({true_count} out of {record_count})")
#             logger.debug(f"Boolean aggregations for {boolean_cols}: Percentage={percentage}%")

#         # Percentage query
#         if is_percentage_prompt(prompt):
#             percentage_match = re.search(r"ROUND\(SUM\(CASE WHEN (.+?) THEN 1 ELSE 0 END\) * 100\.0 / COUNT\(\*\), 2\)", sql, re.IGNORECASE)
#             if percentage_match:
#                 condition = percentage_match.group(1)
#                 condition_clean = re.sub(r"['\"]", "", condition).replace(" = ", " is ").replace(" > ", " exceeds ").replace("APRV_LOAN_PYMT_AM", "loan amount")
#                 percentage = data[0]["percentage_result"] if data else 0
#                 summary.append(f"\nPercentage result: {percentage:.2f}% of records where {condition_clean}")
#                 logger.debug(f"Percentage query detected: {percentage}%")

#         # Fallback for missing metadata
#         if not metadata_available:
#             summary.append("\nNote: Limited metadata available, so column descriptions may be simplified.")

#         # Finalize summary
#         final_summary = "\n".join(summary).strip()
#         logger.info(f"Generated summary: {final_summary}")
#         return final_summary

#     except Exception as e:
#         logger.error(f"Failed to generate summary: {e}")
#         return f"Error generating summary: {str(e)}"












import re
import json
import logging
from mapper_utils import normalize_text, extract_comparative_filters, extract_direct_column_filters, parse_date_range_from_prompt
from db import execute_sql

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed tracing
logger = logging.getLogger(__name__)

# Load business term mappings
try:
    with open("business_mapping.json", "r") as f:
        BUSINESS_TERMS = json.load(f)
except Exception as e:
    logger.error(f"Failed to load business_mapping.json: {e}")
    raise

# Load schema metadata
try:
    with open("schema_metadata.json", "r") as f:
        SCHEMA_METADATA = json.load(f)
except Exception as e:
    logger.error(f"Failed to load schema_metadata.json: {e}")
    raise

def generate_summary_from_result(data, prompt, sql, table_name):
    """Generate a detailed human-readable summary of query results."""
    if not data:
        logger.warning("No records found for summary generation")
        return "No records found for the given query."

    try:
        # Normalize prompt for processing
        prompt_norm = normalize_text(prompt).lower()
        logger.debug(f"Normalized prompt: {prompt_norm}")

        # Extract table metadata
        table_name_upper = table_name.upper()
        table_metadata = SCHEMA_METADATA.get(table_name_upper, {})
        columns_meta = table_metadata.get("columns", {})
        metadata_available = bool(columns_meta)
        logger.debug(f"Metadata available for {table_name_upper}: {metadata_available}")

        # Initialize summary
        summary = []

        # Extract conditions from prompt and SQL
        conditions = []
        business_terms_matched = []
        for key, rule in BUSINESS_TERMS.items():
            if rule["table"].upper() == table_name_upper:
                col = rule["column"]
                val = rule.get("value", "")
                if rule.get("not_null"):
                    conditions.append(f"{col} IS NOT NULL")
                elif rule.get("is_null"):
                    conditions.append(f"{col} IS NULL")
                else:
                    conditions.append(f"{col} = {val}")
                business_terms_matched.append(key)
        # Extract and convert comparative and direct filters to strings
        comparative_filters = extract_comparative_filters(prompt, columns_meta)
        direct_filters = extract_direct_column_filters(prompt, columns_meta)
        conditions.extend(str(f) for f in comparative_filters if f)
        conditions.extend(str(f) for f in direct_filters if f)
        logger.debug(f"Extracted conditions: {conditions}")
        logger.debug(f"Business terms matched: {business_terms_matched}")

        # Date range
        from_dt, to_dt = parse_date_range_from_prompt(prompt)
        date_filter = ""
        date_col = None
        if from_dt and to_dt:
            date_col = next((col for col, meta in columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
            if date_col:
                date_filter = f"from {from_dt} to {to_dt}"
                conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            logger.debug(f"Date filter: {date_filter}")

        # Record count
        record_count = len(data)
        summary.append(f"Found {record_count} {'approved application' if 'approved' in prompt_norm else 'application'} records from {table_name_upper} {date_filter}".strip())

        # Business term counts
        if business_terms_matched:
            summary.append("\nBusiness Term Breakdown:")
            for term in business_terms_matched:
                rule = BUSINESS_TERMS[term]
                col = rule["column"]
                val = rule.get("value", "")
                if rule.get("not_null"):
                    count = sum(1 for row in data if row.get(col) is not None)
                elif rule.get("is_null"):
                    count = sum(1 for row in data if row.get(col) is None)
                else:
                    # Handle boolean and string values correctly
                    if columns_meta.get(col, {}).get("type") == "boolean":
                        target_val = True if str(val) in ("1", "'1'") else False
                    else:
                        target_val = str(val)
                    count = sum(1 for row in data if str(row.get(col)) == str(target_val))
                summary.append(f"- {term.title()}: {count} records")
            logger.debug(f"Business term counts added: {business_terms_matched}")

        # Add other conditions
        if conditions and any(c for c in conditions if not any(c.startswith(f"{rule['column']}") for rule in BUSINESS_TERMS.values())):
            summary.append("\nAdditional Conditions Applied:")
            for cond in conditions:
                if not any(cond.startswith(f"{rule['column']}") for rule in BUSINESS_TERMS.values()):
                    try:
                        # Use column descriptions from schema_metadata
                        for col, meta in columns_meta.items():
                            cond = cond.replace(col, meta.get("desc", col.replace("_", " ").title()))
                        cond_clean = re.sub(r"['\"]", "", cond).replace(" = ", " is ").replace(" > ", " exceeds ")
                        summary.append(f"- {cond_clean}")
                    except TypeError as e:
                        logger.error(f"Failed to clean condition {cond}: {e}")
                        summary.append(f"- {cond} (unprocessed due to format issue)")
            logger.debug(f"Additional conditions added to summary: {conditions}")

        # Numeric averages
        numeric_cols = [col for col in data[0] if col in columns_meta and columns_meta[col].get("type") == "numeric"]
        if numeric_cols:
            summary.append("\nNumeric Averages:")
            for col in numeric_cols:
                col_vals = [row[col] for row in data if row[col] is not None]
                if col_vals:
                    avg = sum(col_vals) / len(col_vals)
                    col_desc = columns_meta.get(col, {}).get("desc", col.replace("_", " ").title())
                    summary.append(f"- Average {col_desc.title()}: ${avg:,.2f}")
            logger.debug(f"Numeric averages for {numeric_cols}")

        # Boolean percentages
        boolean_cols = [col for col in data[0] if col in columns_meta and columns_meta[col].get("type") == "boolean"]
        if boolean_cols:
            summary.append("\nBoolean Insights:")
            for col in boolean_cols:
                true_count = sum(1 for row in data if row.get(col) in (1, True))
                percentage = (true_count / len(data)) * 100 if data else 0
                col_desc = columns_meta.get(col, {}).get("desc", col.replace("_", " ").title())
                summary.append(f"- {col_desc.title()}: {percentage:.2f}% true ({true_count} out of {record_count})")
            logger.debug(f"Boolean aggregations for {boolean_cols}: Percentage={percentage}%")

        # Percentage query detection
        percentage_match = re.search(r"ROUND\s*\(\s*SUM\s*\(\s*CASE\s+WHEN\s+(.+?)\s+THEN\s+1\s+ELSE\s+0\s+END\s*\)\s*\*\s*100\.0\s*/\s*(?:NULLIF\s*\(\s*)?COUNT\s*\(\s*\*\s*\)\s*(?:,\s*0\s*\))?\s*,\s*2\s*\)\s+AS\s+percentage_result", sql, re.IGNORECASE)
        if percentage_match:
            condition = percentage_match.group(1)
            # Replace column names with descriptions
            for col, meta in columns_meta.items():
                condition = condition.replace(col, meta.get("desc", col.replace("_", " ").title()))
            condition_clean = re.sub(r"['\"]", "", condition).replace(" = ", " is ").replace(" > ", " exceeds ")
            percentage = data[0]["percentage_result"] if data and "percentage_result" in data[0] else 0
            summary.append(f"\nPercentage Result: {percentage:.2f}% of records where {condition_clean}")
            logger.debug(f"Percentage query detected: {percentage}%")

        # Finalize summary
        final_summary = "\n".join(summary).strip()
        logger.info(f"Generated summary: {final_summary}")
        return final_summary

    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return f"Error generating summary: {str(e)}"