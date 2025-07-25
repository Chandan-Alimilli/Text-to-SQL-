
def is_percentage_prompt(prompt):
    """Check if prompt requests a percentage calculation."""
    prompt_norm = normalize_text(prompt)
    return any(k in prompt_norm for k in AGGREGATION_KEYWORDS["PERCENTAGE"])













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
    with open("data/business_mapping.json", "r") as f:
        BUSINESS_TERMS = json.load(f)
except Exception as e:
    logger.error(f"Failed to load business_mapping.json: {e}")
    raise

try:
    with open("data/schema_metadata.json", "r") as f:
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

def match_column(prompt, columns_meta):
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
    col = None
    if isinstance(column_candidates, dict):
        col = match_column(prompt, column_candidates)
        if not col and agg_func != "PERCENTAGE":
            for c, meta in column_candidates.items():
                if isinstance(meta, dict) and meta.get("type") == "numeric":
                    col = c
                    logger.debug(f"Fallback to numeric column: {col}")
                    break
    elif isinstance(column_candidates, list):
        col = match_column(prompt, dict(column_candidates))
        col = col or (column_candidates[0][0] if column_candidates else None)
    else:
        logger.error("Invalid column_candidates type")
        raise Exception("❌ Invalid column_candidates type")

    # COUNT can fall back to "APPL_NB"
    if agg_func == "COUNT" and not col:
        col = "APPL_NB"
        logger.debug("Using 'APPL_NB' for COUNT aggregation")

    if not col and agg_func != "PERCENTAGE":
        logger.error("Aggregation column could not be inferred")
        raise Exception("❌ Aggregation column could not be inferred")

    return agg_func, col

def build_aggregation_query(agg_func, column, table, prompt, columns_meta, percentage_condition=None):
    """Build SQL query for aggregation."""
    prompt_norm = normalize_text(prompt)
    conditions = []

    # Business logic conditions for PERCENTAGE
    if agg_func == "PERCENTAGE":
        if not percentage_condition:
            # Try business terms first
            for key, rule in BUSINESS_TERMS.items():
                negated = "non " + key in prompt_norm or "not " + key in prompt_norm
                term_match = "non " + key if "non " + key in prompt_norm else "not " + key if "not " + key in prompt_norm else key
                if term_match in prompt_norm and rule["table"].lower() == table.lower():
                    condition_col = rule["column"].upper()
                    val = rule["value"]
                    val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                    if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
                        if val == "'1'":
                            val = "'0'"
                        elif val == "'0'":
                            val = "'1'"
                        else:
                            stripped_val = val.strip("'")
                            val = f"'Not {stripped_val}'"
                    percentage_condition = f"{condition_col} = {val}"
                    logger.debug(f"Business term condition for percentage: {percentage_condition}")
                    break

        # If no business term, try comparative or direct filters
        if not percentage_condition:
            comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
            direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
            all_filters = comparative_filters + direct_filters
            if all_filters:
                percentage_condition = " AND ".join(all_filters)
                logger.debug(f"Percentage condition from filters: {percentage_condition}")
            else:
                logger.error("Could not infer condition for percentage query")
                raise Exception("❌ Could not infer condition for percentage query")

        # Date range
        from_dt, to_dt = parse_date_range_from_prompt(prompt)
        date_col = next((col.upper() for col, meta in columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
        if date_col:
            if from_dt and to_dt:
                conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            elif from_dt:
                conditions.append(f"{date_col} >= '{from_dt}'")
            elif to_dt:
                conditions.append(f"{date_col} <= '{to_dt}'")
            logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

        # Additional conditions from prompt (excluding percentage_condition)
        additional_comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
        additional_direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
        additional_filters = additional_comparative_filters + additional_direct_filters
        percentage_conditions = set(percentage_condition.split(" AND ")) if percentage_condition else set()
        conditions.extend([f for f in additional_filters if f not in percentage_conditions])

        # Remove duplicates while ensuring only strings
        conditions = list(dict.fromkeys([str(c) for c in conditions if isinstance(c, str)]))
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        numerator = f"COUNT(CASE WHEN {percentage_condition} THEN 1 END)"
        denominator = f"NULLIF(COUNT(*), 0)"
        # Use a generic label if no business term is matched
        label = percentage_condition.split('=')[0].strip().lower().replace('_', '') + "_percentage" if "=" in percentage_condition else "percentage_result"
        return f"SELECT ROUND(100.0 * {numerator} / {denominator}, 2) AS {label} FROM {table}{where_clause}"

    # Business logic conditions for other aggregations
    for key, rule in BUSINESS_TERMS.items():
        negated = "non " + key in prompt_norm or "not " + key in prompt_norm
        term_match = "non " + key if "non " + key in prompt_norm else "not " + key if "not " + key in prompt_norm else key
        if term_match in prompt_norm and rule["table"].lower() == table.lower():
            col = rule["column"].upper()
            if rule.get("not_null"):
                conditions.append(f"{col} IS NOT NULL")
            elif rule.get("is_null"):
                conditions.append(f"{col} IS NULL")
            elif "value" in rule:
                val = rule["value"]
                val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
                    if val == "'1'":
                        val = "'0'"
                    elif val == "'0'":
                        val = "'1'"
                    else:
                        stripped_val = val.strip("'")
                        val = f"'Not {stripped_val}'"
                conditions.append(f"{col} = {val}")
            logger.debug(f"Applied business rule for {term_match}: {col}")

    # Date range for non-percentage aggregations
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    date_col = next((col.upper() for col, meta in columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
    if date_col:
        if from_dt and to_dt:
            conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        elif from_dt:
            conditions.append(f"{date_col} >= '{from_dt}'")
        elif to_dt:
            conditions.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

    # Additional filters
    comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
    direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
    conditions.extend(comparative_filters + direct_filters)
    conditions = list(dict.fromkeys([str(c) for c in conditions if isinstance(c, str)]))  # Remove duplicates
    logger.debug(f"Conditions: {conditions}")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # COUNT query
    if agg_func == "COUNT":
        return f"SELECT COUNT({column}) AS count_{column.lower() if column != '*' else 'all'} FROM {table}{where_clause}"

    # Other aggregations (SUM, AVG, MAX, MIN)
    return f"SELECT {agg_func}({column}) AS {agg_func.lower()}_{column.lower()} FROM {table}{where_clause}"