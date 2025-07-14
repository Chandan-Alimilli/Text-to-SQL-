import psycopg2
from psycopg2.extras import RealDictCursor
import os

# PostgreSQL connection string
POSTGRES_URL = "postgresql://postgres:HtNHeMLTYTFAzuPmSvXwgllgqmBNWdqW@caboose.proxy.rlwy.net:53958/railway"

def get_connection():
    return psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)

def execute_query(sql):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        if cursor.description:  # SELECT query
            rows = cursor.fetchall()
        else:  # INSERT/UPDATE/DELETE
            rows = []
        conn.commit()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print("❌ Error executing query:", e)
        return []
