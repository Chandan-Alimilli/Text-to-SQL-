# snowflake_mapper.py
import spacy
from itertools import combinations
from snowflake_db import get_conn, release_conn

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def get_cached_schema():
    schema = {}
    fk_map = {}
    conn = get_conn()
    cursor = conn.cursor()

    # Fetch all tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = CURRENT_SCHEMA()")
    tables = [row[0].lower() for row in cursor.fetchall()]

    # Fetch all columns
    for table in tables:
        cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table.upper()}'")
        columns = [row[0].lower() for row in cursor.fetchall()]
        schema[table] = columns

    # Fetch foreign keys
    cursor.execute("""
        SELECT
            kcu.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column
        FROM information_schema.referential_constraints rc
        JOIN information_schema.key_column_usage kcu ON rc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON rc.constraint_name = ccu.constraint_name
        WHERE kcu.table_schema = CURRENT_SCHEMA()
    """)
    for row in cursor.fetchall():
        fk_map[(row[0].lower(), row[1].lower())] = (row[2].lower(), row[3].lower())

    release_conn(conn)
    return schema, fk_map

def extract_keywords(prompt):
    doc = nlp(prompt.lower())
    return [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

def score_tables(keywords, schema):
    scores = {}
    for table, columns in schema.items():
        table_score = sum(1 for kw in keywords if kw in table)
        column_score = sum(1 for kw in keywords for col in columns if kw in col)
        scores[table] = table_score + column_score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_scores) > 1 and sorted_scores[0][1] >= sorted_scores[1][1] + 2:
        return [sorted_scores[0]]
    return sorted_scores

def detect_agg_type(keywords):
    agg_keywords = {
        "COUNT": {"how many", "count", "number"},
        "SUM": {"sum", "total", "amount"},
        "AVG": {"average", "mean", "avg"},
        "MAX": {"maximum", "max"},
        "MIN": {"minimum", "min"},
        "SELECT": {"select", "show", "display", "list", "retrieve"}
    }
    joined = " ".join(keywords).lower()
    for agg_type, triggers in agg_keywords.items():
        if any(word in joined or word in keywords for word in triggers):
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
        matched_cols = []
        for col in cols:
            for kw in keywords:
                if col == kw or kw in col:
                    matched_cols.append(f'"{col.upper()}"')
        col_str = ", ".join(matched_cols) if matched_cols else "*"
        if agg == "COUNT":
            return f'SELECT COUNT(*) FROM "{table.upper()}";'
        elif agg == "SUM" and matched_cols:
            return f'SELECT SUM({matched_cols[0]}) FROM "{table.upper()}";'
        else:
            return f'SELECT {col_str} FROM "{table.upper()}" LIMIT 10;'

    elif joins:
        from_tbl, from_col, to_tbl, to_col = joins[0]
        matched_cols = []
        for table in top_tables:
            for col in schema[table]:
                for kw in keywords:
                    if col == kw or kw in col:
                        matched_cols.append(f'"{table.upper()}"."{col.upper()}"')
        col_str = ", ".join(matched_cols) if matched_cols else "*"
        return (
            f'SELECT {col_str} FROM "{from_tbl.upper()}" '
            f'JOIN "{to_tbl.upper()}" ON "{from_tbl.upper()}"."{from_col.upper()}" = "{to_tbl.upper()}"."{to_col.upper()}" LIMIT 10;'
        )

    return "UNSUPPORTED"
