import re
import spacy
from datetime import datetime
from dateutil import parser
from rag_retriever import schema_metadata

nlp = spacy.load("en_core_web_sm")

def extract_entities(prompt):
    doc = nlp(prompt)
    fields = [chunk.text.lower() for chunk in doc.noun_chunks]
    return fields

def parse_date_range(from_date, to_date):
    try:
        from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else None
        to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else None
        return from_dt, to_dt
    except Exception:
        return None, None

def generate_sql_query(prompt, matched_table, from_date=None, to_date=None, limit=25):
    if isinstance(matched_table, str):
        table_name = matched_table
        metadata = schema_metadata.get(table_name, {})
    elif isinstance(matched_table, dict):
        table_name = list(matched_table.keys())[0]
        metadata = matched_table[table_name]
    else:
        raise Exception("Invalid matched_table structure.")

    fields = extract_entities(prompt)
    selected_cols = []

    for col, desc in metadata.get("columns", {}).items():
        for f in fields:
            if f in desc.lower() or f in col.lower():
                selected_cols.append(col)
                break

    if not selected_cols:
        selected_cols = list(metadata.get("columns", {}).keys())[:5]

    query = f"SELECT {', '.join(selected_cols)} FROM {table_name}"

    date_columns = [col for col in metadata.get("columns", {}) if "date" in col.lower() or col.endswith("_DT")]
    if from_date or to_date:
        from_dt, to_dt = parse_date_range(from_date, to_date)
        if date_columns:
            date_col = date_columns[0]
            conditions = []
            if from_dt:
                conditions.append(f"{date_col} >= '{from_dt}'")
            if to_dt:
                conditions.append(f"{date_col} <= '{to_dt}'")
            query += " WHERE " + " AND ".join(conditions)

    query += f" LIMIT {int(limit)}"
    return query
