# db.py
import snowflake.connector
import os
import logging

# Enable logging for debug
logging.basicConfig(level=logging.INFO)

# ❄️ Snowflake connection setup (credentials should be set as env vars)
SNOWFLAKE_CONFIG = {
    "user": os.getenv("SNOWFLAKE_USER", "your_username"),
    "password": os.getenv("SNOWFLAKE_PASSWORD", "your_password"),
    "account": os.getenv("SNOWFLAKE_ACCOUNT", "your_account_id"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "your_warehouse"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "your_database"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "your_schema"),
    "role": os.getenv("SNOWFLAKE_ROLE", "your_role"),
}

def get_conn():
    logging.info("🔌 Connecting to Snowflake...")
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def release_conn(conn):
    logging.info("❎ Closing Snowflake connection")
    conn.close()

def execute_sql(query):
    logging.info(f"🟢 Running query: {query}")
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows] if rows else []
        return result
    except Exception as e:
        logging.error(f"❌ SQL execution failed: {e}")
        return None
    finally:
        cursor.close()
        release_conn(conn)
