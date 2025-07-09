# db.py
import os
import logging
import traceback
from snowflake.snowpark import Session
from dotenv import load_dotenv

load_dotenv()

# ✅ Proxy config (required inside JPMorgan network)
os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
os.environ["NO_PROXY"] = "localhost,127.0.0.1,.jpmchase.net,.jpmorganchase.net,.eks.amazonaws.com"

# ✅ Snowflake Sandbox External Browser Auth Config
SNOWFLAKE_CONFIG = {
    "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
    "user": "F745794",  # Change to your SID
    "authenticator": "externalbrowser",
    "role": "PROD_110575_SS_AUTO_DA_ADM_FR",
    "warehouse": "PROD_110575_DA_AUTO_L_WH",
    "database": "PROD_110575_SANDBOX_DB",
    "schema": "SS_AUTO_DA"
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
        print("🔧 Traceback:")
        traceback.print_exc()
        logging.warning("⚠️ Snowflake connection failed; fallback logic may be used.")
        return None

def execute_sql(query):
    global session
    if not session:
        get_connection()
    if not session:
        return []

    try:
        df = session.sql(query).collect()
        return [row.as_dict() for row in df]
    except Exception as e:
        print(f"❌ SQL Execution error: {e}")
        return []
