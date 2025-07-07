

import spacy
from itertools import combinations
import sqlite3


try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


DB_PATH = "chase_demo.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def release_conn(conn):
    conn.close()


def get_cached_schema():
    schema = {}
    fk_map = {}
    conn = get_conn()
    cursor = conn.cursor()


    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]


    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cursor.fetchall()]
        schema[table] = columns


    for table in tables:
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        for row in cursor.fetchall():
            from_col = row[3]
            to_table = row[2]
            to_col = row[4]
            fk_map[(table, from_col)] = (to_table, to_col)

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
        "COUNT": {"how many", "count", "number", "total count"},
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
                    matched_cols.append(col)

        col_str = ", ".join(matched_cols) if matched_cols else "*"

        if agg == "COUNT":
            return f"SELECT COUNT(*) FROM {table};"
        elif agg == "SUM" and matched_cols:
            return f"SELECT SUM({matched_cols[0]}) FROM {table};"
        else:
            return f"SELECT {col_str} FROM {table} LIMIT 10;"

 
    elif joins:
        from_tbl, from_col, to_tbl, to_col = joins[0]
        matched_cols = []

        for table in top_tables:
            for col in schema[table]:
                for kw in keywords:
                    if col == kw or kw in col:
                        matched_cols.append(f"{table}.{col}")

        col_str = ", ".join(matched_cols) if matched_cols else "*"

        return (
            f"SELECT {col_str} FROM {from_tbl} "
            f"JOIN {to_tbl} ON {from_tbl}.{from_col} = {to_tbl}.{to_col} LIMIT 10;"
        )

    return "UNSUPPORTED"
