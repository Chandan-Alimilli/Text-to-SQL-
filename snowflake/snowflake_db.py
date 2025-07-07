# snowflake_db.py
import snowflake.connector
import os

# Proxy config (required inside JPMC network)
os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
os.environ["NO_PROXY"] = "jpmorganchase.net,169.254.169.254"

# Snowflake credentials
SNOWFLAKE_CONFIG = {
    "user": "F745794",
    "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
    "warehouse": "PROD_110575_DA_AUTO_WH",
    "database": "PROD_110575_ICDW_DB",
    "schema": "AUTO_V",
    "authenticator": "externalbrowser",  # or "snowflake" if using password
}

def get_conn():
    return snowflake.connector.connect(**SNOWFLAKE_CONFIG)

def release_conn(conn):
    conn.close()

def execute_sql(query: str):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]
        release_conn(conn)
        return result
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return [{"error": str(e)}]
