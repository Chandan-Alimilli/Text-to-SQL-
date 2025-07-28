

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
        # Prioritize matching column based on prompt content
        col = match_column(prompt, column_candidates)
        if not col and agg_func != "PERCENTAGE":
            # Match based on description or column name in prompt
            for c, meta in column_candidates.items():
                if isinstance(meta, dict) and meta.get("type") == "numeric" and agg_func in ["SUM", "AVG", "MAX", "MIN"]:
                    if any(keyword in prompt_norm for keyword in [meta.get("desc", "").lower(), c.lower()]):
                        col = c
                        logger.debug(f"Matched numeric column: {col}")
                        break
                elif isinstance(meta, dict) and meta.get("type") in ["string", "boolean"] and agg_func == "COUNT":
                    if any(keyword in prompt_norm for keyword in [meta.get("desc", "").lower(), c.lower()]):
                        col = c
                        logger.debug(f"Matched non-numeric column: {col}")
                        break
            # Fallback to first suitable column
            if not col:
                for c, meta in column_candidates.items():
                    if isinstance(meta, dict) and meta.get("type") == "numeric" and agg_func in ["SUM", "AVG", "MAX", "MIN"]:
                        col = c
                        logger.debug(f"Fallback to numeric column: {col}")
                        break
                    elif isinstance(meta, dict) and meta.get("type") in ["string", "boolean"] and agg_func == "COUNT":
                        col = c
                        logger.debug(f"Fallback to non-numeric column: {col}")
                        break
    elif isinstance(column_candidates, list):
        col = match_column(prompt, dict(column_candidates))
        col = col or (column_candidates[0][0] if column_candidates else None)
    else:
        logger.error("Invalid column_candidates type")
        raise Exception("❌ Invalid column_candidates type")

    # COUNT can fall back to "ACCT_NB"
    if agg_func == "COUNT" and not col:
        col = "ACCT_NB"
        logger.debug("Using 'ACCT_NB' for COUNT aggregation")

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

    # Business logic conditions for PERCENTAGE
    if agg_func == "PERCENTAGE":
        if percentage_condition:
            # Use percentage_condition for numerator
            table_columns_meta = METADATA.get(table_name, columns_meta)
            comparative_filters, filtered_columns = extract_comparative_filters(prompt, table_columns_meta)
            direct_filters = extract_direct_column_filters(prompt, table_columns_meta, filtered_columns=filtered_columns)
            comparative_filters = list(comparative_filters)
            direct_filters = list(direct_filters)
            all_filters = comparative_filters + direct_filters
            if all_filters:
                percentage_condition = f"{percentage_condition} AND {' AND '.join(all_filters)}" if percentage_condition else " AND ".join(all_filters)
                logger.debug(f"Updated percentage condition with filters: {percentage_condition}")

            # Date range (only add to WHERE clause)
            from_dt, to_dt = parse_date_range_from_prompt(prompt)
            date_col = next((col.upper() for col, meta in table_columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
            if date_col and (from_dt or to_dt):
                if from_dt and to_dt:
                    conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
                elif from_dt:
                    conditions.append(f"{date_col} >= '{from_dt}'")
                elif to_dt:
                    conditions.append(f"{date_col} <= '{to_dt}'")
                logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

            # Remove duplicates
            conditions = list(dict.fromkeys([str(c) for c in conditions if isinstance(c, str)]))
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            numerator = f"COUNT(CASE WHEN {percentage_condition} THEN 1 END)"
            denominator = f"NULLIF(COUNT(*), 0)" if not percentage_denominator_condition else f"NULLIF(COUNT(CASE WHEN {percentage_denominator_condition} THEN 1 END), 0)"
            label = "percentage_result"
            return f"SELECT ROUND(100.0 * {numerator} / {denominator}, 2) AS {label} FROM {table_name}{where_clause}"

    # Business logic conditions for other aggregations
    if agg_func in ["COUNT", "SUM", "AVG", "MAX", "MIN"]:
        table_columns_meta = METADATA.get(table_name, columns_meta)
        comparative_filters, filtered_columns = extract_comparative_filters(prompt, table_columns_meta)
        direct_filters = extract_direct_column_filters(prompt, table_columns_meta, filtered_columns=filtered_columns)
        all_filters = comparative_filters + direct_filters
        if all_filters:
            conditions.extend(all_filters)
            logger.debug(f"Applied filters for {agg_func} query: {all_filters}")

        # Date range
        from_dt, to_dt = parse_date_range_from_prompt(prompt)
        date_col = next((col.upper() for col, meta in table_columns_meta.items() if meta.get("type") in ["date", "timestamp"]), None)
        if date_col and (from_dt or to_dt):
            if from_dt and to_dt:
                conditions.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
            elif from_dt:
                conditions.append(f"{date_col} >= '{from_dt}'")
            elif to_dt:
                conditions.append(f"{date_col} <= '{to_dt}'")
            logger.debug(f"Applied date range: {from_dt} to {to_dt} on {date_col}")

        # Remove duplicates
        conditions = list(dict.fromkeys([str(c) for c in conditions if isinstance(c, str)]))
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        if agg_func == "COUNT":
            return f"SELECT COUNT({column}) AS count_{column.lower() if column != '*' else 'all'} FROM {table_name}{where_clause}"
        return f"SELECT {agg_func}({column}) AS {agg_func.lower()}_{column.lower()} FROM {table_name}{where_clause}"