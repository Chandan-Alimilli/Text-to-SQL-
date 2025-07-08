# snowflake_mapper.py
import logging
import spacy
from itertools import combinations
from snowflake_db import get_conn, release_conn

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Fallback schema if INFORMATION_SCHEMA is blocked
HARDCODED_SCHEMA = {
    "PROD_110575_ICDW_DB.AUTO_V.V_ORIG_SMN_FNCE_ORGN_REFN_CLSE": [
        "APPL_NB", "LOAN_BK_TS", "INSRT_DT", "SRC_SYS_CD", "LIEN_HLDR_NM", "VHCL_FEE_AM", "ORGN_LOAN_PYF_AM", "ADDL_FEE_AM"
    ],
    "PROD_110575_ICDW_DB.AUTO_V.V_ACAPS_ACCT_AUTO_D": [
        "SRC_SYS_CD", "STATE_CD", "VHCL_RGST_NB", "STATE_ALOW_IN", "INDS_CLS_CD", "MEMB_ID", "LIEN_HLDR_NM", "ACCT_NB", "CURR_BAL_AM"
    ]
}

SCHEMA_CACHE = None
FK_MAP_CACHE = None

def get_cached_schema():
    global SCHEMA_CACHE, FK_MAP_CACHE
    if SCHEMA_CACHE is not None and FK_MAP_CACHE is not None:
        return SCHEMA_CACHE, FK_MAP_CACHE

    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS")
        rows = cursor.fetchall()

        schema = {}
        for row in rows:
            full_table = f"{row[0]}.{row[1]}.{row[2]}"
            if full_table not in schema:
                schema[full_table] = []
            schema[full_table].append(row[3])

        cursor.execute("SELECT TABLE_NAME, COLUMN_NAME, FOREIGN_TABLE_NAME, FOREIGN_COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE POSITION_IN_UNIQUE_CONSTRAINT IS NOT NULL")
        fk_rows = cursor.fetchall()

        fk_map = {}
        for row in fk_rows:
            from_tbl, from_col, to_tbl, to_col = row
            fk_map[(from_tbl, from_col)] = (to_tbl, to_col)

        release_conn(conn)
        SCHEMA_CACHE = schema
        FK_MAP_CACHE = fk_map
        return schema, fk_map

    except Exception as e:
        logging.warning(f"❌ Failed to fetch schema from INFORMATION_SCHEMA. Using hardcoded fallback. Reason: {e}")
        return HARDCODED_SCHEMA, {}  # fallback with no join support

def extract_keywords(prompt):
    doc = nlp(prompt.lower())
    return [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

def score_tables(keywords, schema):
    scores = {}
    for table, columns in schema.items():
        table_score = sum(1 for kw in keywords if kw in table.lower())
        column_score = sum(1 for kw in keywords for col in columns if kw in col.lower())
        scores[table] = table_score + column_score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_scores) > 1 and sorted_scores[0][1] >= sorted_scores[1][1] + 2:
        return [sorted_scores[0]]
    return sorted_scores

def detect_agg_type(keywords):
    agg_keywords = {
        "COUNT": {"how many", "count", "number", "total count"},
        "SUM": {"sum", "total", "amount"},
        "AVG": {"average", "mean", "avg"},
        "MAX": {"maximum", "max"},
        "MIN": {"minimum", "min"},
        "SELECT": {"select", "show", "display", "list", "retrieve"}
    }
    joined = " ".join(keywords).lower()
    for agg_type, triggers in agg_keywords.items():
        if any(word in joined for word in triggers):
            return agg_type
    return "SELECT"

def find_join_path(tables, fk_map):
    joins = []
    used = set()
    for t1, t2 in combinations(tables, 2):
        for (from_tbl, from_col), (to_tbl, to_col) in fk_map.items():
            if (from_tbl == t1 and to_tbl == t2) or (from_tbl == t2 and to_tbl == t1):
                joins.append((from_tbl, from_col, to_tbl, to_col))
                used.update({t1, t2})
                break
    return joins if len(used) == len(tables) else []

def generate_sql_query(slots):
    prompt = slots.get("prompt", "")
    schema, fk_map = get_cached_schema()
    keywords = extract_keywords(prompt)
    scored = score_tables(keywords, schema)
    top_tables = [table for table, score in scored if score > 0][:2]

    if not top_tables:
        return "UNSUPPORTED"

    joins = find_join_path(top_tables, fk_map)
    agg = detect_agg_type(keywords)

    if len(top_tables) == 1:
        table = top_tables[0]
        cols = schema[table]
        matched_cols = [col for col in cols if any(kw in col.lower() for kw in keywords)]
        col_str = ", ".join(matched_cols) if matched_cols else "*"

        if agg == "COUNT":
            return f'SELECT COUNT(*) FROM "{table}";'
        elif agg == "SUM" and matched_cols:
            return f'SELECT SUM({matched_cols[0]}) FROM "{table}";'
        else:
            return f'SELECT {col_str} FROM "{table}" LIMIT 10;'

    elif joins:
        from_tbl, from_col, to_tbl, to_col = joins[0]
        matched_cols = []
        for table in top_tables:
            for col in schema[table]:
                if any(kw in col.lower() for kw in keywords):
                    matched_cols.append(f"{table}.{col}")

        col_str = ", ".join(matched_cols) if matched_cols else "*"
        return (
            f'SELECT {col_str} FROM "{from_tbl}" '
            f'JOIN "{to_tbl}" ON "{from_tbl}".{from_col} = "{to_tbl}".{to_col} LIMIT 10;'
        )

    return "UNSUPPORTED"

def summarize_response(prompt, rows):
    return f"Fetched {len(rows)} records for: '{prompt}'"
