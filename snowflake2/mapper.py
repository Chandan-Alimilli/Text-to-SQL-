import re
from typing import Dict

# 🔹 Manually defined schema from all 5 Excel screenshots
HARDCODED_SCHEMA = {
    "auto_fnce_orgn_refn_clse_fee": [
        "APPL_NB", "LOAN_BK_TS", "SNPST_DT", "SRC_SYS_CD", "LOAN_BK_ET_TS",
        "LIEN_HLDR_NM", "VHCL_FEE_AM", "ORGN_LOAN_PYF_AM", "ADDL_FEE_AM",
        "EFF_DT", "ETL_TS"
    ],
    "afnc_dsi_orgn_acct_dy": [
        "ACCT_NB", "APPL_APRV_IN", "APPL_ELGC_CNTRT_IN", "APPL_INIT_DT", "APPL_INIT_TS",
        "APPL_NB", "APRV_LOAN_AM", "APRV_LOAN_PYMT_AM", "APRV_PYMT_AM", "APPL_TERM_MO_CN",
        "AUTO_FNCE_ACCT_DIM_ID", "AUTO_FNCE_ORGN_DIM_ID", "BK_DT", "BK_IN", "COAP_BRTH_DT",
        "COAP_FRST_NM", "COAP_LAST_NM", "COAP_MDL_NM", "DLR_DBA_NM", "FINL_DCSN_ACTV_TYPE_CD",
        "FINL_DCSN_DT", "FINL_DCSN_METH_TYPE_CD", "FINL_DCSN_WRKR_STD_ID",
        "FST_DCSN_ACTV_TYPE_CD", "FST_DCSN_DT", "FST_DCSN_METH_TYPE_CD",
        "FST_DCSN_WRKR_STD_ID", "ORGN_CNCL_NM", "ORGN_LOAN_AM", "ORGN_LOAN_PYMT_AM",
        "ORGN_SRC_SYS_CD", "PRIM_APPLNT_BRTH_DT", "PRIM_APPLNT_FRST_NM", "PRIM_APPLNT_LAST_NM",
        "PRIM_APPLNT_MDL_NM", "PRIM_APPLNT_TAX_GOVT_ISSU_ID", "SNPST_DT", "STATE_CD", "STR_NB",
        "STR_NM", "STR_TYPE_CD", "SVRC_SRC_SYS_CD", "UNIT_NB", "VHCL_ID_NB", "VHCL_MAKE_NM",
        "VHCL_MODL_NM", "VHCL_MODL_YR_NB", "VHCL_TRIM_NM", "VHCL_WRNTY_AM"
    ],
    "auto_fnce_orgn_refn_elig": [
        "REFN_ELG_SYS_ID", "RQST_ID", "ENTP_CUST_ID", "SNPST_DT", "SRC_SYS_CD", "STATE_CD",
        "VHCL_RGST_NB", "STATE_ALOW_IN", "INDS_CLS_CD", "MEMB_ID", "LIEN_HLDR_NM", "ACCT_NB",
        "CURR_BAL_AM", "ACCT_OPN_DT", "ACCT_OPN_IN", "STS_EFF_DT", "MINM_MO_CN", "REFN_ELG_IN",
        "FST_RSN_CD", "FST_RSN_DESC_TX", "SCND_RSN_CD", "SCND_RSN_DESC_TX", "THRD_RSN_CD",
        "THRD_RSN_DESC_TX", "FRTH_RSN_CD", "FRTH_RSN_DESC_TX", "FFTH_RSN_CD", "FFTH_RSN_DESC_TX",
        "SIXT_RSN_CD", "SIXT_RSN_DESC_TX", "SEVN_RSN_CD", "SEVN_RSN_DESC_TX", "VHCL_ID_NB",
        "SNPST_DT", "ETL_TS"
    ],
    "auto_fnce_orgn_refn_clse": [
        "APPL_NB", "CLSE_TASK_STG_TX", "CLSE_TASK_STG_STS_TX", "CLSE_TASK_CRE_TS",
        "SNPST_DT", "SRC_SYS_CD", "CLSE_TASK_CRE_ET_TS", "UPDT_USR_ID", "EFF_DT", "ETL_TS"
    ],
    "auto_fnce_orgn_refn_clse_fee": [
        "APPL_NB", "LOAN_BK_TS", "SNPST_DT", "SRC_SYS_CD", "LOAN_BK_ET_TS",
        "LIEN_HLDR_NM", "VHCL_FEE_AM", "ORGN_LOAN_PYF_AM", "ADDL_FEE_AM", "EFF_DT", "ETL_TS"
    ]
}

# 🔹 Extract keywords (lowercase + remove special chars)
def extract_keywords(prompt: str):
    prompt = re.sub(r"[^\w\s]", " ", prompt.lower())
    return prompt.split()

# 🔹 Find best matching table based on keyword hits
def match_table(prompt: str):
    keywords = extract_keywords(prompt)
    table_scores = {}

    for table, columns in HARDCODED_SCHEMA.items():
        score = sum(any(kw in col.lower() for col in columns) for kw in keywords)
        table_scores[table] = score

    return max(table_scores, key=table_scores.get) if table_scores else None

# 🔹 Build the SQL query
def generate_sql_query(prompt: str):
    if isinstance(prompt, dict):
        prompt = prompt.get("prompt", "")
    elif not isinstance(prompt, str):
        return ""

    table = match_table(prompt)
    if not table:
        return "SELECT 'No matching table found';"

    keywords = extract_keywords(prompt)
    columns = HARDCODED_SCHEMA.get(table, [])
    matched_columns = [col for col in columns if any(kw in col.lower() for kw in keywords)]

    if not matched_columns:
        matched_columns = columns[:5]

    column_list = ', '.join(matched_columns)
    return f"SELECT {column_list} FROM {table};"

# 🔹 Simple summarizer
def summarize_response(prompt: str, result: list):
    if not result:
        return "No records found."
    return f"Found {len(result)} results matching your request."
