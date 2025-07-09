import os
import logging
import snowflake.connector
from snowflake.connector.errors import Error

# ✅ Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ✅ Proxy configuration for JPMC
os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
os.environ["NO_PROXY"] = "jpmorganchase.net,169.254.169.254"

# ✅ Snowflake credentials (replace password before running)
SNOWFLAKE_CONFIG = {
    "user": "F745794",
    "password": "",  
    "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
    "warehouse": "PROD_110575_DA_AUTO_WH",
    "database": "PROD_110575_ICDW_DB",
    "schema": "AUTO_V"
}

# ✅ Attempt to connect to Snowflake and fetch schema
SCHEMA_CACHE = {}
CONNECTED = False

def try_connect_snowflake():
    global CONNECTED
    try:
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        CONNECTED = True
        logger.info("✅ Snowflake connection established.")
        return conn
    except Error as e:
        CONNECTED = False
        logger.error("❌ Snowflake connection failed.")
        logger.error(f"🔍 Reason: {str(e)}")
        logger.warning("⚠️ Snowflake connection failed; fallback logic may be used.")
        return None

def get_connection():
    if not CONNECTED:
        return None
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def execute_sql(sql: str):
    conn = get_connection()
    if not conn:
        logger.warning("⚠️ No connection. Returning empty result.")
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in result]
    except Exception as e:
        logger.error(f"❌ SQL execution failed: {e}")
        return []
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def fetch_dynamic_schema():
    conn = try_connect_snowflake()
    if not conn:
        return None

    schema = {}
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = '{SNOWFLAKE_CONFIG['schema']}'
            ORDER BY table_name, ordinal_position;
        """)
        for table, column in cursor.fetchall():
            if table not in schema:
                schema[table] = []
            schema[table].append(column)
        cursor.close()
        conn.close()
        return schema
    except Exception as e:
        logger.error(f"❌ Failed to fetch schema: {e}")
        return None
