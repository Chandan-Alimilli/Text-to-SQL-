

# import json
# import os
# import difflib

# # Load schema metadata
# with open("schema_metadata.json", "r", encoding="utf-8") as f:
#     SCHEMA_META = json.load(f)

# def fuzzy_match(term, options, threshold=0.6):
#     """
#     Return the best fuzzy match from options based on similarity threshold.
#     """
#     matches = difflib.get_close_matches(term.lower(), options, n=1, cutoff=threshold)
#     return matches[0] if matches else None

# def retrieve_relevant_table(prompt):
#     """
#     Identify the most relevant table and columns from the schema based on the prompt.
#     """
#     prompt_lower = prompt.lower()
#     best_table = None
#     best_score = 0
#     table_column_map = {}

#     for table, meta in SCHEMA_META.items():
#         table_score = 0
#         column_matches = []

#         # Match table description or name
#         if table.lower() in prompt_lower or meta['description'].lower() in prompt_lower:
#             table_score += 2

#         # Match each column description or name
#         for col, desc in meta['columns'].items():
#             if col.lower() in prompt_lower or desc.lower() in prompt_lower:
#                 column_matches.append(col)
#                 table_score += 1

#         # Fuzzy fallback
#         if not column_matches:
#             for col, desc in meta['columns'].items():
#                 if fuzzy_match(col, prompt.split()) or fuzzy_match(desc, prompt.split()):
#                     column_matches.append(col)

#         # Keep best match table only
#         if table_score > best_score:
#             best_table = table
#             best_score = table_score
#             table_column_map = {col: meta['columns'][col] for col in column_matches if col in meta['columns']}

#     return {best_table: {"description": SCHEMA_META[best_table]['description'], "columns": table_column_map}} if best_table else {}







import json
import os
import spacy
from difflib import SequenceMatcher

nlp = spacy.load("en_core_web_sm")

metadata_path = os.path.join("schema_metadata.json")
with open(metadata_path, "r", encoding="utf-8") as f:
    schema_metadata = json.load(f)

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def retrieve_relevant_table(prompt):
    doc = nlp(prompt.lower())
    tokens = set([token.text for token in doc if not token.is_stop])

    best_score = 0
    best_match = {}

    for table, meta in schema_metadata.items():
        table_score = 0
        matched_columns = {}

        # Check table name in prompt directly
        if table.lower() in prompt.lower():
            table_score += 1.5  # boost score

        for token in tokens:
            if similarity(token, table) > 0.8:
                table_score += 1.0

            for col, desc in meta.get("columns", {}).items():
                if token in col.lower() or token in desc.lower():
                    table_score += 0.3
                    matched_columns[col] = desc

        if table_score > best_score:
            best_score = table_score
            best_match = {
                table: {
                    "description": meta.get("description", ""),
                    "columns": matched_columns if matched_columns else meta.get("columns", {})
                }
            }

    return best_match
