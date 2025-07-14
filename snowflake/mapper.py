import re
import spacy
from datetime import datetime
nlp = spacy.load("en_core_web_sm")

def extract_fields_from_prompt(prompt, table_columns):
    doc = nlp(prompt.lower())
    matched_fields = []

    for token in doc:
        for col, desc in table_columns.items():
            if token.text in desc.lower() or token.text in col.lower():
                matched_fields.append(col)
    return list(set(matched_fields))

def extract_date_filters(from_date, to_date):
    try:
        from_date = datetime.strptime(from_date, "%Y-%m") if from_date else None
        to_date = datetime.strptime(to_date, "%Y-%m") if to_date else None
    except Exception:
        from_date, to_date = None, None
    return from_date, to_date

def generate_sql_query(prompt, matched_table=None, from_date=None, to_date=None, record_limit=25):
    if not matched_table or not isinstance(matched_table, dict):
        raise ValueError("No matched table or invalid format")

    table_name = list(matched_table.keys())[0]
    table_info = matched_table[table_name]
    table_columns = table_info.get("columns", {})

    fields = extract_fields_from_prompt(prompt, table_columns)

    if not fields:
        fields = list(table_columns.keys())

    select_clause = ", ".join(fields)
    query = f"SELECT {select_clause} FROM {table_name}"

    date_col = next((col for col in table_columns if 'date' in col.lower() or col.upper().endswith('_DT')), None)

    from_date, to_date = extract_date_filters(from_date, to_date)
    if from_date and to_date and date_col:
        query += f" WHERE {date_col} >= '{from_date.strftime('%Y-%m-%d')}' AND {date_col} <= '{to_date.strftime('%Y-%m-%d')}'"

    query += f" LIMIT {record_limit}"
    return query






































# import re
# import spacy
# import calendar
# from datetime import datetime
# from typing import Dict, Optional

# nlp = spacy.load("en_core_web_sm")

# def extract_intents(prompt: str):
#     doc = nlp(prompt)
#     nouns = [chunk.text.lower() for chunk in doc.noun_chunks]
#     date_matches = re.findall(r"\d{4}-\d{2}", prompt)
#     return {"nouns": nouns, "dates": date_matches}

# def get_last_day_of_month(year_month: str) -> str:
#     year, month = map(int, year_month.split("-"))
#     last_day = calendar.monthrange(year, month)[1]
#     return f"{year}-{month:02d}-{last_day:02d}"

# def generate_sql_query(prompt: str, matched_table: Dict, from_date: Optional[str] = None, to_date: Optional[str] = None, limit: int = 10) -> str:
#     intents = extract_intents(prompt)
#     table_name = list(matched_table.keys())[0]
#     table_info = matched_table[table_name]
#     column_map = table_info.get("columns", {})

#     selected_cols = []
#     for noun in intents["nouns"]:
#         for col, desc in column_map.items():
#             if noun in desc.lower() or noun in col.lower():
#                 selected_cols.append(col)
    
#     if not selected_cols:
#         selected_cols = list(column_map.keys())[:3]

#     col_str = ", ".join(set(selected_cols))
#     query = f"SELECT {col_str} FROM {table_name}"

#     where_clauses = []

#     if from_date:
#         try:
#             from_date = from_date.strip() + "-01"
#             datetime.strptime(from_date, "%Y-%m-%d")
#             where_clauses.append(f"SNPST_DT >= '{from_date}'")
#         except Exception:
#             pass

#     if to_date:
#         try:
#             to_date_full = get_last_day_of_month(to_date.strip())
#             datetime.strptime(to_date_full, "%Y-%m-%d")
#             where_clauses.append(f"SNPST_DT <= '{to_date_full}'")
#         except Exception:
#             pass

#     if where_clauses:
#         query += " WHERE " + " AND ".join(where_clauses)

#     query += f" LIMIT {limit}"
#     return query
