




# import json
# from difflib import SequenceMatcher
# import os
# import sys

# schema_path = "schema_metadata.json"
# business_terms_path = "business_mapping.json"

# # ✅ Validate schema file
# if not os.path.exists(schema_path):
#     print(f"❌ ERROR: schema file not found: {schema_path}")
#     sys.exit(1)

# # ✅ Validate business mapping file
# if not os.path.exists(business_terms_path):
#     print(f"❌ ERROR: business mapping file not found: {business_terms_path}")
#     sys.exit(1)

# # ✅ Load and preview files
# try:
#     with open(schema_path, "r") as f:
#         schema_content = f.read().strip()
#         if not schema_content:
#             raise ValueError("schema_metadata.json is empty")
#         schema_metadata = json.loads(schema_content)
# except Exception as e:
#     print(f"❌ Error loading schema_metadata.json: {e}")
#     sys.exit(1)

# try:
#     with open(business_terms_path, "r") as f:
#         business_content = f.read().strip()
#         if not business_content:
#             raise ValueError("business_mapping.json is empty")
#         business_terms = json.loads(business_content)
# except Exception as e:
#     print(f"❌ Error loading business_mapping.json: {e}")
#     sys.exit(1)

# # ✅ Similarity utility
# def similarity(a, b):
#     return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# # ✅ Core Table Retrieval Logic
# def retrieve_relevant_table(prompt: str):
#     prompt_lower = prompt.lower()
#     table_scores = {}

#     # 💡 Direct business keyword mapping
#     for keyword, mapping in business_terms.items():
#         if keyword in prompt_lower:
#             matched_table = mapping["table"]
#             return {matched_table: schema_metadata.get(matched_table, {})}

#     # 💡 Approximate matching (fallback)
#     for table, meta in schema_metadata.items():
#         table_score = similarity(prompt_lower, table)
#         if table_score > 0.7:
#             return {table: meta}
#         for col, desc in meta.get("columns", {}).items():
#             score = similarity(prompt_lower, col) + similarity(prompt_lower, desc)
#             table_scores.setdefault(table, 0)
#             table_scores[table] += score

#     # 💡 Pick highest scoring fallback
#     if table_scores:
#         best_table = max(table_scores.items(), key=lambda x: x[1])[0]
#         return {best_table: schema_metadata[best_table]}
    
#     return {}









import json
from difflib import SequenceMatcher
import os
import sys

schema_path = "schema_metadata.json"
business_terms_path = "business_mapping.json"

# ✅ Validate schema file
if not os.path.exists(schema_path):
    print(f"❌ ERROR: schema file not found: {schema_path}")
    sys.exit(1)

if not os.path.exists(business_terms_path):
    print(f"❌ ERROR: business mapping file not found: {business_terms_path}")
    sys.exit(1)

# ✅ Load schema and business terms
try:
    with open(schema_path, "r") as f:
        schema_content = f.read().strip()
        if not schema_content:
            raise ValueError("schema_metadata.json is empty")
        schema_metadata = json.loads(schema_content)
except Exception as e:
    print(f"❌ Error loading schema_metadata.json: {e}")
    sys.exit(1)

try:
    with open(business_terms_path, "r") as f:
        business_content = f.read().strip()
        if not business_content:
            raise ValueError("business_mapping.json is empty")
        business_terms = json.loads(business_content)
except Exception as e:
    print(f"❌ Error loading business_mapping.json: {e}")
    sys.exit(1)

# ✅ Utility
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# 🚫 Generic terms to penalize if used alone
GENERIC_TERMS = {"application", "request", "record", "entry", "data"}

# ✅ Table Retrieval Logic
def retrieve_relevant_table(prompt: str):
    prompt_lower = prompt.lower()
    table_scores = {}

    # ✅ Business Term Override (high confidence)
    for keyword, mapping in business_terms.items():
        if keyword in prompt_lower:
            matched_table = mapping["table"]
            return {matched_table: schema_metadata.get(matched_table, {})}

    # ✅ Compute table scores
    for table, meta in schema_metadata.items():
        score = 0

        # ✅ Boost for matching column names/descriptions
        for col, desc in meta.get("columns", {}).items():
            if col.lower() in prompt_lower or desc.lower() in prompt_lower:
                score += 3
            else:
                score += similarity(prompt_lower, col) + similarity(prompt_lower, desc)

        # 🚫 Penalize generic terms if no strong keyword match
        if any(generic in prompt_lower for generic in GENERIC_TERMS):
            score -= 1

        table_scores[table] = score

    # ✅ Return highest scored table
    if table_scores:
        best_table = max(table_scores.items(), key=lambda x: x[1])[0]
        return {best_table: schema_metadata[best_table]}

    return {}
