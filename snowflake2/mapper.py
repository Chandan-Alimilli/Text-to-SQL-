import re
import json
import spacy
import dateparser
from datetime import datetime
from dateutil import parser
from rag_retriever import schema_metadata
from prompt_utils import extract_limit_from_prompt


nlp = spacy.load("en_core_web_sm")

# ✅ Load business mappings from external JSON file
with open("business_mapping.json", "r") as f:
    BUSINESS_TERMS = json.load(f)

def extract_entities(prompt):
    doc = nlp(prompt)
    return [chunk.text.lower() for chunk in doc.noun_chunks]

def parse_date_range_from_prompt(prompt: str):
    prompt = prompt.lower()
    from_dt, to_dt = None, None

    date_matches = re.findall(r"\d{4}-\d{2}-\d{1,2}", prompt)
    if len(date_matches) == 1:
        from_dt = to_dt = parser.parse(date_matches[0]).strftime("%Y-%m-%d")
    elif len(date_matches) >= 2:
        from_dt = parser.parse(date_matches[0]).strftime("%Y-%m-%d")
        to_dt = parser.parse(date_matches[1]).strftime("%Y-%m-%d")

    elif any(k in prompt for k in ["last", "this", "next", "month", "week", "year", "today", "yesterday"]):
        parsed = dateparser.parse(prompt)
        if parsed:
            from_dt = to_dt = parsed.strftime("%Y-%m-%d")

    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    for i, m in enumerate(months):
        if f"in {m}" in prompt or f"month of {m}" in prompt:
            year = datetime.now().year
            from_dt = f"{year}-{i+1:02d}-01"
            to_dt = f"{year}-{i+1:02d}-28"
        elif f"from {m}" in prompt:
            from_dt = f"{datetime.now().year}-{i+1:02d}-01"
        elif f"to {m}" in prompt:
            to_dt = f"{datetime.now().year}-{i+1:02d}-28"

    return from_dt, to_dt

# def generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata, from_date=None, to_date=None, limit=None):
#     if isinstance(matched_table, str):
#         table_name = matched_table
#         metadata = schema_metadata.get(table_name, {})
#     elif isinstance(matched_table, dict):
#         table_name = list(matched_table.keys())[0]
#         metadata = matched_table[table_name]
#     else:
#         raise Exception("Invalid matched_table structure.")

#     table_name_upper = table_name.upper()
#     prompt_lower = prompt.lower()
#     fields = extract_entities(prompt)
#     selected_cols = []
#     flag_conditions = []

#     # ✅ Business conditions (supporting multiple conditions)
#     for key, rule in BUSINESS_TERMS.items():
#         if key in prompt_lower and rule["table"].lower() == table_name.lower():
#             col = rule["column"].upper()
#             if rule.get("not_null"):
#                 flag_conditions.append(f"{col} IS NOT NULL")
#             elif rule.get("is_null"):
#                 flag_conditions.append(f"{col} IS NULL")
#             elif "value" in rule:
#                 val = rule["value"]
#                 val = f"'{val}'" if isinstance(val, str) else val
#                 flag_conditions.append(f"{col} = {val}")

#     # ✅ Detect count prompt
#     is_count = any(word in prompt_lower for word in ["how many", "count", "number of"])

#     # ✅ Column selection
#     user_specified = False
#     mentioned_indicator = any(key in prompt_lower for key in BUSINESS_TERMS)

#     for col, desc in metadata.get("columns", {}).items():
#         col_upper = col.upper()
#         for f in fields:
#             if f in desc.lower() or f in col.lower():
#                 selected_cols.append(col_upper)
#                 user_specified = True
#                 break

#     if not user_specified or mentioned_indicator:
#         selected_cols = [col.upper() for col in metadata.get("columns", {}).keys()]

#     # ✅ SELECT clause
#     if is_count:
#         query = f"SELECT COUNT(*) AS TOTAL FROM {table_name_upper}"
#     else:
#         query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"

#     # ✅ Date parsing
#     inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
#     from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
#     to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to

#     where_clauses = []
#     if flag_conditions:
#         where_clauses.extend(flag_conditions)

#     # ✅ Smart date column detection
#     date_columns = [
#         col.upper() for col in metadata.get("columns", {})
#         if col.lower().endswith("_dt") or "date" in col.lower()
#     ]
#     if not date_columns:
#         date_columns = [
#             col.upper() for col in metadata.get("columns", {})
#             if col.lower().endswith("_ts") or "timestamp" in col.lower()
#         ]

#     if (from_dt or to_dt) and date_columns:
#         date_col = date_columns[0]
#         if from_dt:
#             where_clauses.append(f"{date_col} >= '{from_dt}'")
#         if to_dt:
#             where_clauses.append(f"{date_col} <= '{to_dt}'")
#         if not is_count and date_col not in selected_cols:
#             selected_cols.append(date_col)

#     # ✅ Final query assembly
#     if where_clauses:
#         query += " WHERE " + " AND ".join(where_clauses)
#     if not is_count:
#         query += f" LIMIT {limit}"

#     return query








from prompt_utils import extract_limit_from_prompt  # ✅ Make sure you have this import

def generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata, from_date=None, to_date=None, limit=None):
    if isinstance(matched_table, str):
        table_name = matched_table
        metadata = schema_metadata.get(table_name, {})
    elif isinstance(matched_table, dict):
        table_name = list(matched_table.keys())[0]
        metadata = matched_table[table_name]
    else:
        raise Exception("Invalid matched_table structure.")

    table_name_upper = table_name.upper()
    prompt_lower = prompt.lower()
    fields = extract_entities(prompt)
    selected_cols = []
    flag_conditions = []

    # ✅ Business conditions (supporting multiple conditions)
    for key, rule in BUSINESS_TERMS.items():
        if key in prompt_lower and rule["table"].lower() == table_name.lower():
            col = rule["column"].upper()
            if rule.get("not_null"):
                flag_conditions.append(f"{col} IS NOT NULL")
            elif rule.get("is_null"):
                flag_conditions.append(f"{col} IS NULL")
            elif "value" in rule:
                val = rule["value"]
                val = f"'{val}'" if isinstance(val, str) else val
                flag_conditions.append(f"{col} = {val}")

    # ✅ Detect count prompt
    is_count = any(word in prompt_lower for word in ["how many", "count", "number of"])

    # ✅ Column selection
    user_specified = False
    mentioned_indicator = any(key in prompt_lower for key in BUSINESS_TERMS)

    for col, desc in metadata.get("columns", {}).items():
        col_upper = col.upper()
        for f in fields:
            if f in desc.lower() or f in col.lower():
                selected_cols.append(col_upper)
                user_specified = True
                break

    if not user_specified or mentioned_indicator:
        selected_cols = [col.upper() for col in metadata.get("columns", {}).keys()]

    # ✅ SELECT clause
    if is_count:
        query = f"SELECT COUNT(*) AS TOTAL FROM {table_name_upper}"
    else:
        query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"

    # ✅ Date parsing
    inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
    from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
    to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to

    where_clauses = []
    if flag_conditions:
        where_clauses.extend(flag_conditions)

    # ✅ Smart date column detection
    date_columns = [
        col.upper() for col in metadata.get("columns", {})
        if col.lower().endswith("_dt") or "date" in col.lower()
    ]
    if not date_columns:
        date_columns = [
            col.upper() for col in metadata.get("columns", {})
            if col.lower().endswith("_ts") or "timestamp" in col.lower()
        ]

    if (from_dt or to_dt) and date_columns:
        date_col = date_columns[0]
        if from_dt:
            where_clauses.append(f"{date_col} >= '{from_dt}'")
        if to_dt:
            where_clauses.append(f"{date_col} <= '{to_dt}'")
        if not is_count and date_col not in selected_cols:
            selected_cols.append(date_col)

    # ✅ WHERE clause
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    # ✅ Use prompt-defined limit or fallback to default 50
    if not is_count:
        final_limit = extract_limit_from_prompt(prompt, default_limit=50)
        query += f" LIMIT {final_limit}"

    return query
