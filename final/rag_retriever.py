import json
import os

# Load schema metadata
with open(os.path.join(os.path.dirname(__file__), 'schema_metadata.json'), 'r') as f:
    metadata = json.load(f)

def get_relevant_tables(prompt: str):
    prompt_lower = prompt.lower()
    matched_tables = []

    for table, info in metadata.items():
        table_desc = info.get("description", "").lower()

        if table.lower() in prompt_lower or table_desc in prompt_lower:
            matched_tables.append(table)
            continue

        for col, desc in info["columns"].items():
            if col.lower() in prompt_lower or desc.lower() in prompt_lower:
                matched_tables.append(table)
                break

    return list(set(matched_tables))

def get_columns_for_table(table: str):
    if table in metadata:
        return metadata[table]["columns"]
    return {}

def get_schema_matches(prompt: str):
    tables = get_relevant_tables(prompt)
    matches = {}

    for table in tables:
        cols = get_columns_for_table(table)
        matched_cols = []
        for col, desc in cols.items():
            if col.lower() in prompt.lower() or desc.lower() in prompt.lower():
                matched_cols.append(col)
        matches[table] = matched_cols if matched_cols else list(cols.keys())[:3]

    return matches
