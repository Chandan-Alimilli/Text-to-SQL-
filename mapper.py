import re
from typing import Dict

# 🔹 Prefix based on your Snowflake config
DB = "PROD_110575_ICDW_DB"
SCHEMA = "AUTO_V"
TABLE_PREFIX = f"{DB}.{SCHEMA}"

# 🔹 Static schema dictionary
HARDCODED_SCHEMA = {
    "afnc_dsi_orgn_acct_dy": [
        "ACCT_NB", "APPL_APRV_IN", "APPL_ELGC_CNTRT_IN", "APPL_INIT_DT", "APPL_INIT_TS",
        "APPL_NB", "APRV_LOAN_AM", "APRV_LOAN_PYMT_AM", "APRV_PYMT_AM", "APPL_TERM_MO_CN"
    ],
    "auto_fnce_orgn_refn_clse_fee": [
        "APPL_NB", "LOAN_BK_TS", "SNPST_DT", "SRC_SYS_CD", "LOAN_BK_ET_TS",
        "LIEN_HLDR_NM", "VHCL_FEE_AM", "ORGN_LOAN_PYF_AM", "ADDL_FEE_AM", "EFF_DT", "ETL_TS"
    ],
    "auto_fnce_orgn_refn_elig": [
        "REFN_ELG_SYS_ID", "RQST_ID", "ENTP_CUST_ID", "SNPST_DT", "SRC_SYS_CD", "STATE_CD",
        "VHCL_RGST_NB", "STATE_ALOW_IN", "INDS_CLS_CD", "MEMB_ID"
    ],
    "auto_fnce_orgn_refn_clse": [
        "APPL_NB", "CLSE_TASK_STG_TX", "CLSE_TASK_STG_STS_TX", "CLSE_TASK_CRE_TS",
        "SNPST_DT", "SRC_SYS_CD", "CLSE_TASK_CRE_ET_TS", "UPDT_USR_ID", "EFF_DT", "ETL_TS"
    ]
}

# 🔹 Optional custom WHERE clause templates
WHERE_CONDITIONS = {
    "afnc_dsi_orgn_acct_dy": """WHERE appl_nb IN (
        SELECT DISTINCT appl_nb
        FROM PROD_110575_ICDW_DB.AUTO_V.AUTO_FNCE_ORGN_DIM
        WHERE UPPER(dgtl_rel_cd) IN (UPPER('sample_id'))
    )""",
    "auto_fnce_fbs_dcsn": "WHERE PQUAL_DCSN_ASES_BY_CD = 'AEGIS'"
}

def extract_keywords(prompt: str):
    prompt = re.sub(r"[^\w\s]", " ", prompt.lower())
    return prompt.split()

def match_table(prompt: str):
    keywords = extract_keywords(prompt)
    table_scores = {}
    for table, columns in HARDCODED_SCHEMA.items():
        score = sum(any(kw in col.lower() for col in columns) for kw in keywords)
        table_scores[table] = score
    best_table = max(table_scores, key=table_scores.get) if table_scores else None
    print("📊 Best matched table:", best_table)
    return best_table

def generate_sql_query(prompt: str):
    if isinstance(prompt, dict):
        prompt = prompt.get("prompt", "")
    elif not isinstance(prompt, str):
        return ""

    print("🔍 Extracting keywords from:", prompt)
    keywords = extract_keywords(prompt)

    # Check for exact table name
    for table in HARDCODED_SCHEMA:
        if table in prompt:
            columns = HARDCODED_SCHEMA[table]
            column_list = ', '.join(columns[:5])
            where_clause = WHERE_CONDITIONS.get(table, "")
            return f"SELECT {column_list} FROM {TABLE_PREFIX}.{table} ds {where_clause};"

    # Fallback: keyword match
    table = match_table(prompt)
    if not table:
        return "SELECT 'No matching table found';"

    columns = HARDCODED_SCHEMA.get(table, [])
    if not columns:
        return "SELECT 'No columns available';"

    matched_columns = [col for col in columns if any(kw in col.lower() for kw in keywords)]
    if not matched_columns:
        matched_columns = columns[:5]

    column_list = ', '.join(matched_columns)
    where_clause = WHERE_CONDITIONS.get(table, "")
    return f"SELECT {column_list} FROM {TABLE_PREFIX}.{table} ds {where_clause};"

def summarize_response(prompt: str, result: list):
    if not result:
        return "No records found."
    return f"Found {len(result)} results matching your request."
