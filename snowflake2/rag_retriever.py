# import json
# import os
# from difflib import SequenceMatcher

# metadata_path = "schema_metadata.json"

# with open(metadata_path, "r") as f:
#     schema_metadata = json.load(f)

# def similarity(a, b):
#     return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# def retrieve_relevant_table(prompt):
#     prompt_lower = prompt.lower()
#     table_scores = {}

#     for table, meta in schema_metadata.items():
#         table_score = similarity(prompt_lower, table)
#         if table_score > 0.7:
#             return {table: meta}

#         for col, desc in meta.get("columns", {}).items():
#             score = similarity(prompt_lower, col) + similarity(prompt_lower, desc)
#             table_scores.setdefault(table, 0)
#             table_scores[table] += score

#     if table_scores:
#         best_table = max(table_scores.items(), key=lambda x: x[1])[0]
#         return {best_table: schema_metadata[best_table]}
#     return {}



















import json
from difflib import SequenceMatcher

schema_path = "schema_metadata.json"
business_terms_path = "business_mapping.json"

with open(schema_path, "r") as f:
    schema_metadata = json.load(f)

with open(business_terms_path, "r") as f:
    business_terms = json.load(f)

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def retrieve_relevant_table(prompt: str):
    prompt_lower = prompt.lower()
    table_scores = {}

    for keyword, mapping in business_terms.items():
        if keyword in prompt_lower:
            matched_table = mapping["table"]
            return {matched_table: schema_metadata.get(matched_table, {})}

    for table, meta in schema_metadata.items():
        table_score = similarity(prompt_lower, table)
        if table_score > 0.7:
            return {table: meta}
        for col, desc in meta.get("columns", {}).items():
            score = similarity(prompt_lower, col) + similarity(prompt_lower, desc)
            table_scores.setdefault(table, 0)
            table_scores[table] += score

    if table_scores:
        best_table = max(table_scores.items(), key=lambda x: x[1])[0]
        return {best_table: schema_metadata[best_table]}
    return {}
