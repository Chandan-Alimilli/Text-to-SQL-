
# import re
# import json
# import spacy
# from fuzzywuzzy import fuzz
# import logging
# from mapper_utils import (
#     parse_date_range_from_prompt,
#     extract_entities,
#     extract_comparative_filters,
#     extract_direct_column_filters,
#     normalize_text
# )

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Load business and metadata mappings
# try:
#     with open("business_mapping.json", "r") as f:
#         BUSINESS_TERMS = json.load(f)
# except Exception as e:
#     logger.error(f"Failed to load business_mapping.json: {e}")
#     raise

# try:
#     with open("schema_metadata.json", "r") as f:
#         METADATA = json.load(f)
# except Exception as e:
#     logger.error(f"Failed to load schema_metadata.json: {e}")
#     raise

# nlp = spacy.load("en_core_web_sm")

# AGGREGATION_KEYWORDS = {
#     "SUM": ["total", "sum", "add up", "aggregate"],
#     "AVG": ["average", "avg", "mean"],
#     "MAX": ["maximum", "max", "highest", "top", "greatest"],
#     "MIN": ["minimum", "min", "lowest", "smallest"],
#     "COUNT": ["how many", "number of", "count", "total records"],
#     "PERCENTAGE": ["percentage", "percent", "%"]
# }

# def match_column(prompt, columns_meta, agg_func=None):
#     """Match a column based on prompt using fuzzy matching and lemmatization."""
#     prompt_norm = normalize_text(prompt)
#     best_match = (None, 0)
#     for col, meta in columns_meta.items():
#         col_name = col.lower()
#         col_desc = meta.get("desc", "").lower()
#         score = max(
#             fuzz.partial_ratio(prompt_norm, col_name),
#             fuzz.partial_ratio(prompt_norm, col_desc)
#         )
#         # Prioritize numeric columns for AVG, SUM, MAX, MIN
#         if agg_func in ["AVG", "SUM", "MAX", "MIN"] and meta.get("type") == "numeric":
#             score += 10  # Boost numeric columns for these aggregations
#         if score > best_match[1]:
#             best_match = (col, score)
#     if best_match[1] >= 60:
#         logger.debug(f"Matched column: {best_match[0]} with score {best_match[1]}")
#         return best_match[0]
#     logger.warning(f"No column matched for prompt: {prompt}")
#     return None

# def detect_aggregation(prompt, column_candidates):
#     """Detect aggregation function and column from prompt."""
#     prompt_raw = prompt.lower()
#     prompt_norm = normalize_text(prompt)
#     agg_func = None
#     col = None

#     # Early match for COUNT and SUM
#     if "how many" in prompt_raw or "number of" in prompt_raw or "count of" in prompt_raw:
#         agg_func = "COUNT"
#         logger.debug("Detected COUNT aggregation from prompt")
#     elif "sum of" in prompt_raw or "total" in prompt_raw:
#         agg_func = "SUM"
#         logger.debug("Detected SUM aggregation from prompt")
#     else:
#         for func, keywords in AGGREGATION_KEYWORDS.items():
#             if any(kw in prompt_norm for kw in keywords):
#                 agg_func = func
#                 logger.debug(f"Detected aggregation: {func}")
#                 break

#     if not agg_func:
#         logger.error("Aggregation type not recognized")
#         raise Exception("❌ Aggregation type not recognized")

#     # Handle column matching
#     if isinstance(column_candidates, dict):
#         if agg_func in ["AVG", "SUM", "MAX", "MIN"]:
#             # For AVG, SUM, MAX, MIN, prioritize numeric columns
#             col = match_column(prompt, column_candidates, agg_func)
#             if not col:
#                 # Fallback to first numeric column
#                 for c, meta in column_candidates.items():
#                     if isinstance(meta, dict) and meta.get("type") == "numeric":
#                         col = c
#                         logger.debug(f"Fallback to numeric column: {col}")
#                         break
#         elif agg_func == "COUNT":
#             # For COUNT, use '*' to count all rows and rely on WHERE clause for filters
#             col = "*"
#             logger.debug("Using '*' for COUNT aggregation")
#         else:
#             # For other aggregations, match normally
#             col = match_column(prompt, column_candidates)
#             if not col:
#                 for c, meta in column_candidates.items():
#                     if isinstance(meta, dict) and meta.get("type") in ["string", "boolean"]:
#                         col = c
#                         logger.debug(f"Fallback to non-numeric column: {col}")
#                         break
#     elif isinstance(column_candidates, list):
#         col = match_column(prompt, dict(column_candidates), agg_func)
#         if not col and agg_func == "COUNT":
#             col = "*"
#             logger.debug("Using '*' for COUNT aggregation")
#         elif not col:
#             col = column_candidates[0][0] if column_candidates else None
#     else:
#         logger.error("Invalid column_candidates type")
#         raise Exception("❌ Invalid column_candidates type")

#     if not col and agg_func != "PERCENTAGE":
#         logger.error("Aggregation column could not be inferred")
#         raise Exception("❌ Aggregation column could not be inferred")

#     return agg_func, col

# def build_aggregation_query(agg_func, column, table, prompt, columns_meta, percentage_condition=None, percentage_denominator_condition=None):
#     """Build SQL query for aggregation, handling multiple conditions."""
#     prompt_norm = normalize_text(prompt)
#     prompt_lower = prompt.lower()
#     conditions = []
#     table_name = table

#     # Extract all filters (business terms, comparative, and direct)
#     table_columns_meta = METADATA.get(table_name, columns_meta)
#     comparative_filters, filtered_columns = extract_comparative_filters(prompt, table_columns_meta)
#     direct_filters = extract_direct_column_filters(prompt, table_columns_meta, filtered_columns=filtered_columns)
#     all_filters = list(comparative_filters) + list(direct_filters)

#     # Handle business terms for conditions (e.g., approved, booked)
#     for term, rule in BUSINESS_TERMS.items():
#         term_lower = term.lower()
#         negated = False
#         term_match = term_lower
#         if f"non {term_lower}" in prompt_lower or f"not {term_lower}" in prompt_lower:
#             negated = True
#             term_match = f"non {term_lower}" if f"non {term_lower}" in prompt_lower else f"not {term_lower}"
#         if term_match in prompt_lower and rule["table"].upper() == table_name:
#             col = rule["column"].upper()
#             if rule.get("not_null"):
#                 condition = f"{col} IS NOT NULL"
#             elif rule.get("is_null"):
#                 condition = f"{col} IS NULL"
#             elif "value" in rule:
#                 val = rule["value"]
#                 val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
#                 if negated:
#                     if val == "'1'":
#                         val = "'0'"
#                     elif val == "'0'":
#                         val = "'1'"
#                     else:
#                         stripped_val = val.strip("'")
#                         val = f"'Not {stripped_val}'"
#                 condition = f"{col} = {val}"
#             else:
#                 continue
#             all_filters.append(condition)
#             logger.debug(f"Applied business term condition: {condition} for term {term_match}")

#     # Date range
#     from_dt, to_dt = parse_date_range_from_prompt(prompt)
#     date_col = next((col.upper() for col, meta in table_columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
#     if date_col and (from_dt or to_dt):
#         if from_dt and to_dt:
#             all_filters.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
#         elif from_dt:
#             all_filters.append(f"{date_col} >= '{from_dt}'")
#         elif to_dt:
#             all_filters.append(f"{date_col} <= '{to_dt}'")
#         logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

#     # Remove duplicates
#     all_filters = list(dict.fromkeys([str(c) for c in all_filters if isinstance(c, str)]))
#     where_clause = " WHERE " + " AND ".join(all_filters) if all_filters else ""

#     # Business logic for PERCENTAGE
#     if agg_func == "PERCENTAGE":
#         if percentage_condition:
#             percentage_condition = f"{percentage_condition} AND {' AND '.join(all_filters)}" if all_filters else percentage_condition
#             logger.debug(f"Updated percentage condition with filters: {percentage_condition}")
#         elif all_filters:
#             percentage_condition = " AND ".join(all_filters)
#             logger.debug(f"Set percentage condition from filters: {percentage_condition}")
#         numerator = f"COUNT(CASE WHEN {percentage_condition} THEN 1 END)" if percentage_condition else "COUNT(*)"
#         denominator = f"NULLIF(COUNT(*), 0)" if not percentage_denominator_condition else f"NULLIF(COUNT(CASE WHEN {percentage_denominator_condition} THEN 1 END), 0)"
#         label = "percentage_result"
#         return f"SELECT ROUND(100.0 * {numerator} / {denominator}, 2) AS {label} FROM {table_name}{where_clause}"

#     # Business logic for other aggregations
#     if agg_func in ["COUNT", "SUM", "AVG", "MAX", "MIN"]:
#         if agg_func == "COUNT":
#             return f"SELECT COUNT(*) AS count_result FROM {table_name}{where_clause}"
#         return f"SELECT {agg_func}({column}) AS {agg_func.lower()}_{column.lower()} FROM {table_name}{where_clause}"






































import re
import json
import spacy
from fuzzywuzzy import fuzz
import logging
from mapper_utils import (
    parse_date_range_from_prompt,
    extract_entities,
    extract_comparative_filters,
    extract_direct_column_filters,
    normalize_text
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load business and metadata mappings
try:
    with open("business_mapping.json", "r") as f:
        BUSINESS_TERMS = json.load(f)
except Exception as e:
    logger.error(f"Failed to load business_mapping.json: {e}")
    raise

try:
    with open("schema_metadata.json", "r") as f:
        METADATA = json.load(f)
except Exception as e:
    logger.error(f"Failed to load schema_metadata.json: {e}")
    raise

nlp = spacy.load("en_core_web_sm")

AGGREGATION_KEYWORDS = {
    "SUM": ["total", "sum", "add up", "aggregate"],
    "AVG": ["average", "avg", "mean"],
    "MAX": ["maximum", "max", "highest", "top", "greatest"],
    "MIN": ["minimum", "min", "lowest", "smallest"],
    "COUNT": ["how many", "number of", "count", "total records"],
    "PERCENTAGE": ["percentage", "percent", "%"]
}

def match_column(prompt, columns_meta, agg_func=None):
    """Match a column based on prompt using fuzzy matching and lemmatization."""
    prompt_norm = normalize_text(prompt)
    best_match = (None, 0)
    for col, meta in columns_meta.items():
        col_name = col.lower()
        col_desc = meta.get("desc", "").lower()
        score = max(
            fuzz.partial_ratio(prompt_norm, col_name),
            fuzz.partial_ratio(prompt_norm, col_desc)
        )
        # Prioritize numeric columns for AVG, SUM, MAX, MIN
        if agg_func in ["AVG", "SUM", "MAX", "MIN"] and meta.get("type") == "numeric":
            score += 10  # Boost numeric columns for these aggregations
        if score > best_match[1]:
            best_match = (col, score)
    if best_match[1] >= 60:
        logger.debug(f"Matched column: {best_match[0]} with score {best_match[1]}")
        return best_match[0]
    logger.warning(f"No column matched for prompt: {prompt}")
    return None

def detect_aggregation(prompt, column_candidates):
    """Detect aggregation function and column from prompt."""
    prompt_raw = prompt.lower()
    prompt_norm = normalize_text(prompt)
    agg_func = None
    col = None

    # Early match for COUNT and SUM
    if "how many" in prompt_raw or "number of" in prompt_raw or "count of" in prompt_raw:
        agg_func = "COUNT"
        logger.debug("Detected COUNT aggregation from prompt")
    elif "sum of" in prompt_raw or "total" in prompt_raw:
        agg_func = "SUM"
        logger.debug("Detected SUM aggregation from prompt")
    else:
        for func, keywords in AGGREGATION_KEYWORDS.items():
            if any(kw in prompt_norm for kw in keywords):
                agg_func = func
                logger.debug(f"Detected aggregation: {func}")
                break

    if not agg_func:
        logger.error("Aggregation type not recognized")
        raise Exception("❌ Aggregation type not recognized")

    # Handle column matching
    if isinstance(column_candidates, dict):
        if agg_func in ["AVG", "SUM", "MAX", "MIN"]:
            # For AVG, SUM, MAX, MIN, prioritize numeric columns
            col = match_column(prompt, column_candidates, agg_func)
            if not col:
                # Fallback to first numeric column
                for c, meta in column_candidates.items():
                    if isinstance(meta, dict) and meta.get("type") == "numeric":
                        col = c
                        logger.debug(f"Fallback to numeric column: {col}")
                        break
        elif agg_func == "COUNT":
            # For COUNT, use '*' to count all rows and rely on WHERE clause for filters
            col = "*"
            logger.debug("Using '*' for COUNT aggregation")
        else:
            # For other aggregations, match normally
            col = match_column(prompt, column_candidates)
            if not col:
                for c, meta in column_candidates.items():
                    if isinstance(meta, dict) and meta.get("type") in ["string", "boolean"]:
                        col = c
                        logger.debug(f"Fallback to non-numeric column: {col}")
                        break
    elif isinstance(column_candidates, list):
        col = match_column(prompt, dict(column_candidates), agg_func)
        if not col and agg_func == "COUNT":
            col = "*"
            logger.debug("Using '*' for COUNT aggregation")
        elif not col:
            col = column_candidates[0][0] if column_candidates else None
    else:
        logger.error("Invalid column_candidates type")
        raise Exception("❌ Invalid column_candidates type")

    if not col and agg_func != "PERCENTAGE":
        logger.error("Aggregation column could not be inferred")
        raise Exception("❌ Aggregation column could not be inferred")

    return agg_func, col

def build_aggregation_query(agg_func, column, table, prompt, columns_meta, percentage_condition=None, percentage_denominator_condition=None):
    """Build SQL query for aggregation, handling multiple conditions."""
    prompt_norm = normalize_text(prompt)
    prompt_lower = prompt.lower()
    conditions = []
    table_name = table

    # Extract all filters (comparative and direct)
    table_columns_meta = METADATA.get(table_name, columns_meta)
    comparative_filters, filtered_columns = extract_comparative_filters(prompt, table_columns_meta)
    direct_filters = extract_direct_column_filters(prompt, table_columns_meta, filtered_columns=filtered_columns)
    additional_filters = list(comparative_filters) + list(direct_filters)

    # Date range
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    date_col = next((col.upper() for col, meta in table_columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
    if date_col and (from_dt or to_dt):
        if from_dt and to_dt:
            additional_filters.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        elif from_dt:
            additional_filters.append(f"{date_col} >= '{from_dt}'")
        elif to_dt:
            additional_filters.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

    # Handle business terms for percentage conditions
    numerator_conditions = []
    denominator_conditions = []
    percentage_match = re.search(r"percentage of ([\w\s]+?)(?: applications)?(?:\s+over\s+([\w\s]+?)(?: applications)?)?(?:\s|$)", prompt_lower)
    if percentage_match:
        numerator_terms = [term.strip() for term in percentage_match.group(1).split(" and ")]
        denominator_term = percentage_match.group(2)
        # Numerator conditions
        for term in numerator_terms:
            term_lower = term.lower()
            rule = BUSINESS_TERMS.get(term_lower)
            if rule and rule["table"].upper() == table_name:
                col = rule["column"].upper()
                if rule.get("not_null"):
                    condition = f"{col} IS NOT NULL"
                elif rule.get("is_null"):
                    condition = f"{col} IS NULL"
                elif "value" in rule:
                    val = rule["value"]
                    val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                    condition = f"{col} = {val}"
                else:
                    continue
                if condition not in numerator_conditions:
                    numerator_conditions.append(condition)
                    logger.debug(f"Added numerator condition: {condition} for term {term_lower}")
        # Denominator conditions
        if denominator_term:
            term_lower = denominator_term.strip().lower()
            terms = [term.strip() for term in term_lower.split(" and ")]
            for term in terms:
                rule = BUSINESS_TERMS.get(term)
                if rule and rule["table"].upper() == table_name:
                    col = rule["column"].upper()
                    if rule.get("not_null"):
                        condition = f"{col} IS NOT NULL"
                    elif rule.get("is_null"):
                        condition = f"{col} IS NULL"
                    elif "value" in rule:
                        val = rule["value"]
                        val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                        condition = f"{col} = {val}"
                    else:
                        continue
                    if condition not in denominator_conditions:
                        denominator_conditions.append(condition)
                        logger.debug(f"Added denominator condition: {condition} for term {term}")
    else:
        # Handle business terms for numerator if no "over" clause
        for term, rule in BUSINESS_TERMS.items():
            term_lower = term.lower()
            negated = False
            term_match = term_lower
            if f"non {term_lower}" in prompt_lower or f"not {term_lower}" in prompt_lower:
                negated = True
                term_match = f"non {term_lower}" if f"non {term_lower}" in prompt_lower else f"not {term_lower}"
            if term_match in prompt_lower and rule["table"].upper() == table_name:
                col = rule["column"].upper()
                if rule.get("not_null"):
                    condition = f"{col} IS NOT NULL"
                elif rule.get("is_null"):
                    condition = f"{col} IS NULL"
                elif "value" in rule:
                    val = rule["value"]
                    val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                    if negated:
                        if val == "'1'":
                            val = "'0'"
                        elif val == "'0'":
                            val = "'1'"
                        else:
                            stripped_val = val.strip("'")
                            val = f"'Not {stripped_val}'"
                    condition = f"{col} = {val}"
                else:
                    continue
                if condition not in numerator_conditions:
                    numerator_conditions.append(condition)
                    logger.debug(f"Added numerator condition: {condition} for term {term_match}")

    # Remove duplicates
    additional_filters = list(dict.fromkeys([str(c) for c in additional_filters if isinstance(c, str)]))
    numerator_conditions = list(dict.fromkeys([str(c) for c in numerator_conditions if isinstance(c, str)]))
    denominator_conditions = list(dict.fromkeys([str(c) for c in denominator_conditions if isinstance(c, str)]))

    # Combine filters for WHERE clause (only additional filters like date or comparative/direct)
    where_clause = " WHERE " + " AND ".join(additional_filters) if additional_filters else ""

    # Business logic for PERCENTAGE
    if agg_func == "PERCENTAGE":
        # Use provided percentage_condition if available, otherwise use numerator_conditions
        effective_numerator = percentage_condition or (" AND ".join(numerator_conditions) if numerator_conditions else None)
        effective_denominator = percentage_denominator_condition or (" AND ".join(denominator_conditions) if denominator_conditions else None)
        numerator = f"COUNT(CASE WHEN {effective_numerator} THEN 1 END)" if effective_numerator else "COUNT(*)"
        denominator = f"NULLIF(COUNT(CASE WHEN {effective_denominator} THEN 1 END), 0)" if effective_denominator else "NULLIF(COUNT(*), 0)"
        label = "percentage_result"
        return f"SELECT ROUND(100.0 * {numerator} / {denominator}, 2) AS {label} FROM {table_name}{where_clause}"

    # Business logic for other aggregations
    if agg_func in ["COUNT", "SUM", "AVG", "MAX", "MIN"]:
        # Combine all filters for non-percentage aggregations
        all_filters = numerator_conditions + additional_filters
        all_filters = list(dict.fromkeys([str(c) for c in all_filters if isinstance(c, str)]))
        where_clause = " WHERE " + " AND ".join(all_filters) if all_filters else ""
        if agg_func == "COUNT":
            return f"SELECT COUNT(*) AS count_result FROM {table_name}{where_clause}"
        return f"SELECT {agg_func}({column}) AS {agg_func.lower()}_{column.lower()} FROM {table_name}{where_clause}"