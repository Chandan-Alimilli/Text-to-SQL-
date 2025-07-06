


# import sqlite3
# import os

# # Create or connect to the SQLite database
# DB_PATH = "chase_demo.db"
# conn = sqlite3.connect(DB_PATH, check_same_thread=False)
# cursor = conn.cursor()

# def setup_database():
#     """Initialize the database using schema.sql"""
#     try:
#         schema_path = os.path.join("data", "schema.sql")
#         with open(schema_path, "r") as f:
#             schema_sql = f.read()
#         cursor.executescript(schema_sql)
#         conn.commit()
#         print("✅ Database initialized from schema.sql")
#     except Exception as e:
#         print(f"❌ Failed to set up database: {e}")

# def execute_sql(query: str):
#     """Execute a SQL query and return results as list of dictionaries"""
#     try:
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         columns = [desc[0] for desc in cursor.description]
#         return [dict(zip(columns, row)) for row in rows]
#     except Exception as e:
#         print(f"❌ SQL execution error: {e}")
#         return [{"error": str(e)}]






import psycopg2
import os
from psycopg2.extras import RealDictCursor

# PostgreSQL URL
DATABASE_URL = "postgresql://postgres:JpqdXMBPXZqftuMThUgUBXnpzPgsXVOd@tramway.proxy.rlwy.net:44410/railway"


# Connect to PostgreSQL
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()

def setup_database():
    """Initialize the database using schema.sql (optional if DB is preconfigured)"""
    try:
        schema_path = os.path.join("data", "schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ PostgreSQL database initialized from schema.sql")
    except Exception as e:
        print(f"❌ Failed to set up PostgreSQL database: {e}")

def execute_sql(query: str):
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        conn.rollback()  # 🔥 This line is critical for PostgreSQL
        print(f"❌ SQL execution error: {e}")
        return [{"error": str(e)}]

