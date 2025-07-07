







import spacy
from itertools import combinations
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# 🔹 Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# 🔹 PostgreSQL DB
DATABASE_URL = "postgresql://postgres:JpqdXMBPXZqftuMThUgUBXnpzPgsXVOd@tramway.proxy.rlwy.net:44410/railway"

# 🔹 DB connection pool
POSTGRES_POOL = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_conn():
    return POSTGRES_POOL.getconn()

def release_conn(conn):
    POSTGRES_POOL.putconn(conn)

# 🔹 Cache schema and FK map
SCHEMA_CACHE = None
FK_MAP_CACHE = None

def get_cached_schema():
    global SCHEMA_CACHE, FK_MAP_CACHE
    if SCHEMA_CACHE and FK_MAP_CACHE:
        return SCHEMA_CACHE, FK_MAP_CACHE

    conn = get_conn()
    cursor = conn.cursor()

    schema = {}
    fk_map = {}

    # Tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tables = [row[0] for row in cursor.fetchall()]

    # Columns
    for table in tables:
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s;
        """, (table,))
        columns = [row[0] for row in cursor.fetchall()]
        schema[table] = columns

    # Foreign Keys
    cursor.execute("""
        SELECT
            tc.table_name AS from_table,
            kcu.column_name AS from_column,
            ccu.table_name AS to_table,
            ccu.column_name AS to_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY';
    """)
    for row in cursor.fetchall():
        fk_map[(row[0], row[1])] = (row[2], row[3])

    release_conn(conn)

    SCHEMA_CACHE = schema
    FK_MAP_CACHE = fk_map
    return schema, fk_map

# 🔹 NLP utilities
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

# 🔹 Main SQL generator
def generate_sql_query(slots, use_value_matching=False):
    prompt = slots.get("prompt", "")
    schema, fk_map = get_cached_schema()
    conn = get_conn()
    cursor = conn.cursor()

    # 🔹 Step 1: Value match (optional)
    def find_value_matches(value):
        matches = []
        for table, columns in schema.items():
            for col in columns:
                try:
                    query = f"SELECT * FROM {table} WHERE {col} ILIKE %s LIMIT 1;"
                    cursor.execute(query, (f"%{value}%",))
                    if cursor.fetchone():
                        matches.append((table, col, value))
                except Exception:
                    continue
        return matches

    if use_value_matching:
        tokens = [token.text for token in nlp(prompt) if token.is_alpha and not token.is_stop]
        value_filters = []
        for token in tokens:
            value_filters.extend(find_value_matches(token))

        if value_filters:
            results = []
            seen_rows = set()
            combined_queries = []
            for table, col, val in value_filters:
                cursor.execute(f"SELECT * FROM {table} WHERE {col} ILIKE %s LIMIT 5", (f"%{val}%",))
                rows = cursor.fetchall()
                for row in rows:
                    row_tuple = tuple(row.items())
                    if (table, row_tuple) not in seen_rows:
                        results.append(f"-- {table}: {row}")
                        seen_rows.add((table, row_tuple))
                combined_queries.append(f"SELECT * FROM {table} WHERE {col} ILIKE '%{val}%' LIMIT 5;")
            release_conn(conn)
            return "\n".join(combined_queries + results)

    # 🔹 Step 2: Keyword-based SQL
    keywords = extract_keywords(prompt)
    scored = score_tables(keywords, schema)
    top_tables = [table for table, score in scored if score > 0][:2]
    if not top_tables:
        release_conn(conn)
        return "UNSUPPORTED"

    joins = find_join_path(top_tables, fk_map)
    agg = detect_agg_type(keywords)

    if len(top_tables) == 1:
        table = top_tables[0]
        cols = schema[table]
        matched_cols = [col for col in cols if any(kw in col for kw in keywords)]
        col_str = ", ".join(matched_cols) if matched_cols else "*"
        release_conn(conn)
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
            matched_cols.extend([
                f"{table}.{col}" for col in schema[table] if any(kw in col for kw in keywords)
            ])
        col_str = ", ".join(matched_cols) if matched_cols else "*"

        where_clause = ""
        if "new york" in prompt.lower():
            if "branches" in top_tables:
                where_clause = (
                    f" WHERE {from_tbl}.branch_location ILIKE '%New York%'"
                    if from_tbl == "branches"
                    else f" WHERE {to_tbl}.branch_location ILIKE '%New York%'"
                )

        release_conn(conn)
        return (
            f"SELECT {col_str} FROM {from_tbl} "
            f"JOIN {to_tbl} ON {from_tbl}.{from_col} = {to_tbl}.{to_col}{where_clause} LIMIT 10;"
        )

    release_conn(conn)
    return "UNSUPPORTED"
