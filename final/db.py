import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:HtNHeMLTYTFAzuPmSvXwgllgqmBNWdqW@caboose.proxy.rlwy.net:53958/railway")

def run_query(sql):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        result = [dict(zip(headers, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print("❌ DB Error:", e)
        return []
