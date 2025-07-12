import os
import logging
import traceback
from snowflake.snowpark import Session
from dotenv import load_dotenv

load_dotenv()

# ✅ JPM proxy config
os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.jpmchase.net,.jpmorganchase.net,.eks.amazonaws.com"

# ✅ Snowflake connection config
SNOWFLAKE_CONFIG = {
    "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
    "user": "F745794",
    "authenticator": "externalbrowser",
    "role": "PROD_110776_ANL_QRY_FR",
    "warehouse": "PROD_110575_DA_AUTO_L_WH",
    "database": "PROD_110575_ICDW_DB",
    "schema": "AUTO_V"
}

session = None
fallback_notice = ""

def get_connection():
    global session
    try:
        session = Session.builder.configs(SNOWFLAKE_CONFIG).create()
        print("✅ Snowflake session established successfully.")
        return session
    except Exception as e:
        global fallback_notice
        fallback_notice = f"❌ Snowflake connection failed.\n🔍 Reason: {str(e)}"
        print(fallback_notice)
        traceback.print_exc()
        return None

def execute_sql(query):
    global session
    try:
        # 🔄 Reconnect if session is missing or closed
        if not session or session._conn._session._conn.is_closed():
            print("⚠️ Session closed or not found. Reconnecting...")
            session = get_connection()

        if not session:
            print("❌ No active Snowflake session.")
            return []

        df = session.sql(query).collect()
        return [row.as_dict() for row in df]

    except Exception as e:
        print(f"❌ SQL Execution error: {e}")
        return []
