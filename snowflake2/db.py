# db.py
import os
import snowflake.connector
from dotenv import load_dotenv
import logging

load_dotenv()

# Proxy config for JPMorgan (if needed)
os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.jpmchase.net,.jpmorganchase.net,.eks"

# Snowflake credentials
SNOWFLAKE_CONFIG = {
    "user": "F745794",
    "authenticator": "externalbrowser",
    "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
    "warehouse": "PROD_110575_DA_AUTO_L_WH",
    "database": "PROD_110575_ICDW_DB",
    "schema": "AUTO_V",
    "role": "PROD_110575_SS_AUTO_DA_ADM_FR"
}

fallback_notice = ""

def get_connection():
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        print("✅ Connected to Snowflake successfully.")
        return conn
    except Exception as e:
        global fallback_notice
        fallback_notice = f"❌ Snowflake connection failed.\n🔍 Reason: {e}"
        print(fallback_notice)
        logging.warning("⚠️ Snowflake connection failed; fallback logic may be used.")
        return None

def execute_sql(query):
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ SQL Execution error: {e}")
        return []
    finally:
        if conn:
            conn.close()
