
import sqlite3
import os

# Path to your local SQLite DB file
DB_PATH = "chase_demo.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

def setup_database():
    """Initialize the database from schema.sql"""
    try:
        schema_path = os.path.join("schema.sql")
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ SQLite database initialized from schema.sql")
    except Exception as e:
        print(f"❌ Failed to set up SQLite database: {e}")

def execute_sql(query: str):
    """Execute a SQL query and return results as list of dictionaries"""
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return [{"error": str(e)}]
