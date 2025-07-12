import re

# ✅ Qualified Snowflake path
DB = "PROD_110575_ICDW_DB"
SCHEMA = "AUTO_V"
TABLE_PREFIX = f"{DB}.{SCHEMA}"

# ✅ Table → Column mapping (quoted case-sensitive names)
HARDCODED_SCHEMA = {
    "afnc_dsi_orgn_acct_dy": [
        "APPL_NB", "BK_IN", "APPL_APRV_IN"
    ],
    "auto_fnce_orgn_dim": [
        "APPL_NB", "DGTL_REL_CD"
    ],
    "auto_fnce_fbs_dcsn": [
        "PQUAL_STS_CD", "RCRD_CRE_ET_TS", "PQUAL_DCSN_ASES_BY_CD"
    ],
    "afnc_orgn_dim_dy": [
        "ACTN1_DESC_TX", "ORGN_PRTL_TYPE_CD"
    ],
    "auto_fnce_orgn_refn_elig": [
        "MEMB_ID", "ACCT_NB", "SRC_SYS_CD"
    ]
}

# ✅ Optional table-specific WHERE conditions
WHERE_CONDITIONS = {
    "afnc_dsi_orgn_acct_dy": f"""WHERE "APPL_NB" IN (
    SELECT DISTINCT "APPL_NB"
    FROM {TABLE_PREFIX}.auto_fnce_orgn_dim
    WHERE UPPER("DGTL_REL_CD") IN (UPPER('58235a8f-7ee9-44f2-9c9f-4adfa53124bb'))
)""",
    "afnc_orgn_dim_dy": """WHERE "ACTN1_DESC_TX" IS NOT NULL AND "ORGN_PRTL_TYPE_CD" = 'D2D'""",
    "auto_fnce_fbs_dcsn": """WHERE "PQUAL_DCSN_ASES_BY_CD" = 'AEGIS'"""
}

# 🔍 Extract keywords from prompt
def extract_keywords(prompt: str):
    prompt = re.sub(r"[^\w\s]", " ", prompt.lower())
    return prompt.split()

# 🧠 Find best matching table
def match_table(prompt: str):
    keywords = extract_keywords(prompt)
    table_scores = {}
    for table, cols in HARDCODED_SCHEMA.items():
        score = sum(any(kw in col.lower() for col in cols) for kw in keywords)
        table_scores[table] = score
    return max(table_scores, key=table_scores.get) if table_scores else None

# 🔧 Build query logic
def generate_sql_query(prompt: str):
    if isinstance(prompt, dict):
        prompt = prompt.get("prompt", "")
    elif not isinstance(prompt, str):
        return ""

    print("🧠 Prompt:", prompt)
    keywords = extract_keywords(prompt)

    for table in HARDCODED_SCHEMA:
        if table in prompt:
            return build_query(table, keywords)

    table = match_table(prompt)
    if table:
        return build_query(table, keywords)

    return "SELECT 'No matching table found';"

# 🏗️ Construct the SQL query
def build_query(table: str, keywords: list):
    columns = HARDCODED_SCHEMA.get(table, [])
    matched_cols = [col for col in columns if any(kw in col.lower() for kw in keywords)]
    if not matched_cols:
        matched_cols = columns[:5]

    # ✅ Safely quote column names
    column_list = ", ".join(f'"{col}"' for col in matched_cols)
    where_clause = WHERE_CONDITIONS.get(table.lower(), "")
    return f"""SELECT {column_list}
FROM {TABLE_PREFIX}.{table} ds
{where_clause}"""

# 📊 Response summary
def summarize_response(prompt: str, result: list):
    if not result:
        return "No records found."
    return f"Found {len(result)} results matching your request."
