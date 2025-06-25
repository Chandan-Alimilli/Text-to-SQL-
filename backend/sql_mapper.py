
import sqlite3
import spacy
from itertools import combinations

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Automatically download model if not found (for local dev)
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

DB_PATH = "chase_demo.db"

def get_schema_with_fks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    schema = {}
    fk_map = {}

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for (table,) in cursor.fetchall():
        if table.startswith("sqlite_"):  # skip internal
            continue

        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        schema[table] = columns

        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for fk in cursor.fetchall():
            ref_table = fk[2]
            from_col = fk[3]
            to_col = fk[4]
            fk_map[(table, from_col)] = (ref_table, to_col)

    conn.close()
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
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def detect_agg_type(keywords):
    joined = " ".join(keywords)
    if "how many" in joined or "count" in keywords or "number" in keywords:
        return "COUNT"
    if "sum" in keywords or "total" in keywords:
        return "SUM"
    return "SELECT"

def find_join_path(tables, fk_map):
    joins = []
    used = set()

    for t1, t2 in combinations(tables, 2):
        for (from_tbl, from_col), (to_tbl, to_col) in fk_map.items():
            if (from_tbl == t1 and to_tbl == t2) or (from_tbl == t2 and to_tbl == t1):
                joins.append((from_tbl, from_col, to_tbl, to_col))
                used.add(t1)
                used.add(t2)
                break

    return joins if len(used) == len(tables) else []

def generate_sql_query(slots):
    import sqlite3
    prompt = slots.get("prompt", "")
    conn = sqlite3.connect(DB_PATH)
    schema, fk_map = get_schema_with_fks()

    def find_value_matches(value, schema, conn):
        cursor = conn.cursor()
        matches = []
        for table, columns in schema.items():
            for col in columns:
                try:
                    query = f"SELECT * FROM {table} WHERE {col} LIKE ? LIMIT 1"
                    cursor.execute(query, (f"%{value}%",))
                    row = cursor.fetchone()
                    if row:
                        matches.append((table, col, value))
                except sqlite3.OperationalError:
                    continue
        return matches

    # Step 1: Check for direct value match
    tokens = [token.text for token in nlp(prompt) if token.is_alpha and not token.is_stop]
    value_filters = []
    for token in tokens:
        value_matches = find_value_matches(token, schema, conn)
        if value_matches:
            value_filters.extend(value_matches)

    if value_filters:
        results = []
        seen_rows = set()
        combined_queries = []
        for table, col, val in value_filters:
            cursor = conn.cursor()
            query = f"SELECT * FROM {table} WHERE {col} LIKE '%{val}%' LIMIT 5;"
            cursor.execute(f"SELECT * FROM {table} WHERE {col} LIKE ? LIMIT 5", (f"%{val}%",))
            rows = cursor.fetchall()
            for row in rows:
                if (table, row) not in seen_rows:
                    results.append(f"-- {table}: {row}")
                    seen_rows.add((table, row))
            combined_queries.append(query)

        conn.close()
        return "\n".join(combined_queries + results)

    # Step 2: Regular dynamic SQL flow
    keywords = extract_keywords(prompt)
    scored = score_tables(keywords, schema)
    top_tables = [table for table, score in scored if score > 0][:2]
    if not top_tables:
        conn.close()
        return "UNSUPPORTED"

    joins = find_join_path(top_tables, fk_map)
    agg = detect_agg_type(keywords)

    if len(top_tables) == 1:
        table = top_tables[0]
        cols = schema[table]
        matched_cols = [col for col in cols if any(kw in col for kw in keywords)]
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
            matched_cols.extend([f"{table}.{col}" for col in schema[table] if any(kw in col for kw in keywords)])
        col_str = ", ".join(matched_cols) if matched_cols else "*"

        where_clause = ""
        if "new york" in prompt.lower():
            if "branches" in top_tables:
                where_clause = f" WHERE {from_tbl}.location LIKE '%New York%'" if from_tbl == "branches" else f" WHERE {to_tbl}.location LIKE '%New York%'"

        return f"SELECT {col_str} FROM {from_tbl} JOIN {to_tbl} ON {from_tbl}.{from_col} = {to_tbl}.{to_col}{where_clause} LIMIT 10;"

    conn.close()
    return "UNSUPPORTED"
