
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
    "PERCENTAGE": ["conversion rate", "percentage", "percent"]
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

    # Early match for COUNT
    if "how many" in prompt_raw or "number of" in prompt_raw:
        agg_func = "COUNT"
        logger.debug("Detected COUNT aggregation from prompt")

    # Try lemmatized matches
    if not agg_func:
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

    # COUNT can fall back to "*"
    if agg_func == "COUNT" and not col:
        col = "*"
        logger.debug("Using '*' for COUNT aggregation")

    if not col and agg_func != "PERCENTAGE":
        logger.error("Aggregation column could not be inferred")
        raise Exception("❌ Aggregation column could not be inferred")

    return agg_func, col

def build_aggregation_query(agg_func, column, table, prompt, columns_meta):
    """Build SQL query for aggregation."""
    prompt_norm = normalize_text(prompt)
    conditions = []

    # Business logic conditions
    for key, rule in BUSINESS_TERMS.items():
        if key in prompt_norm and rule["table"].lower() == table.lower():
            col = rule["column"].upper()
            if rule.get("not_null"):
                conditions.append(f"{col} IS NOT NULL")
            elif rule.get("is_null"):
                conditions.append(f"{col} IS NULL")
            elif "value" in rule:
                val = rule["value"]
                val = str(val).upper() if isinstance(val, bool) else f"'{val}'"
                conditions.append(f"{col} = {val}")
            logger.debug(f"Applied business rule for {key}: {col}")

    # Date range (using updated mapper_utils function)
    from_dt, to_dt = parse_date_range_from_prompt(prompt)
    date_col = next((col.upper() for col, meta in columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
    if date_col:
        if from_dt:
            conditions.append(f"{date_col} >= '{from_dt}'")
        if to_dt:
            conditions.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

    # Filters from prompt
    conditions += extract_comparative_filters(prompt, columns_meta)
    conditions += extract_direct_column_filters(prompt, columns_meta)
    logger.debug(f"Conditions: {conditions}")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    # COUNT query
    if agg_func == "COUNT":
        return f"SELECT COUNT({column}) AS count_{column.lower() if column != '*' else 'all'} FROM {table}{where_clause}"

    # PERCENTAGE query
    elif agg_func == "PERCENTAGE":
        # Try to find a condition from prompt (boolean, numeric, or categorical)
        condition = None
        doc = nlp(prompt.lower())

        # Check for boolean column first
        condition_col = match_column(prompt, columns_meta)
        if condition_col and columns_meta.get(condition_col, {}).get("type") == "boolean":
            # Determine boolean value (true/false) from prompt
            bool_value = "1" if any(w in prompt.lower() for w in ["approved", "eligible", "booked", "true"]) else "0"
            if any(w in prompt.lower() for w in ["rejected", "not approved", "not eligible", "false"]):
                bool_value = "0"
            condition = f"{condition_col.upper()} = {bool_value}"
            logger.debug(f"Boolean condition for percentage: {condition}")
        else:
            # Check comparative filters (e.g., "loan amount > 5000")
            comp_filters = extract_comparative_filters(prompt, columns_meta)
            if comp_filters:
                condition = comp_filters[0]
                logger.debug(f"Comparative condition for percentage: {condition}")
            else:
                # Check direct filters (e.g., "state code NY")
                direct_filters = extract_direct_column_filters(prompt, columns_meta)
                if direct_filters:
                    condition = direct_filters[0]
                    logger.debug(f"Direct condition for percentage: {condition}")

        # Fallback to first boolean column if no condition found
        if not condition:
            condition_col = next(
                (col for col, meta in columns_meta.items() if meta.get("type") == "boolean"),
                None
            )
            if condition_col:
                condition = f"{condition_col.upper()} = 1"
                logger.debug(f"Fallback boolean condition: {condition}")
            else:
                logger.error("Could not infer condition for percentage query")
                raise Exception("❌ Could not infer condition for percentage query")

        numerator = f"SUM(CASE WHEN {condition} THEN 1 ELSE 0 END)"
        denominator = f"COUNT(*)"
        return f"SELECT ROUND({numerator} * 100.0 / {denominator}, 2) AS percentage_result FROM {table}{where_clause}"

    # Other aggregations (SUM, AVG, MAX, MIN)
    else:
        return f"SELECT {agg_func}({column}) AS {agg_func.lower()}_{column.lower()} FROM {table}{where_clause}"

def is_percentage_prompt(prompt):
    """Check if prompt requests a percentage calculation."""
    prompt_norm = normalize_text(prompt)
    return any(k in prompt_norm for k in AGGREGATION_KEYWORDS["PERCENTAGE"])