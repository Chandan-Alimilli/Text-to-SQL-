

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# PostgreSQL connection string
POSTGRES_URL = "postgresql://postgres:rodbbXXAtvbTseqxaaGHxGMkLWNaRawl@crossover.proxy.rlwy.net:48319/railway"

def get_connection():
    return psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)

def execute_sql(sql):
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






# import os
# import logging
# import traceback
# from snowflake.snowpark import Session

# # ------------------------------------------------------------------------------
# # ✅ Logging
# # ------------------------------------------------------------------------------
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
# )
# logger = logging.getLogger("db")

# # ------------------------------------------------------------------------------
# # ✅ JPM Proxy Setup
# # ------------------------------------------------------------------------------
# os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
# os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
# os.environ["NO_PROXY"] = "localhost,127.0.0.1,.jpmchase.net,.jpmorganchase.net,.eks.amazonaws.com"

# # ------------------------------------------------------------------------------
# # ✅ Snowflake Config
# # ------------------------------------------------------------------------------
# SNOWFLAKE_CONFIG = {
#     "account": "ccpbawsuseast1vps.hassium.us-east-1.aws",
#     "user": "F745794",
#     "authenticator": "externalbrowser",
#     "role": "PROD_110575_DA_AUTO_WH_FR",
#     "warehouse": "PROD_110575_DA_AUTO_L_WH",
#     "database": "PROD_110575_ICDW_DB",
#     "schema": "AUTO_V"
# }

# # ------------------------------------------------------------------------------
# # ✅ Return a new Snowflake session
# # ------------------------------------------------------------------------------
# def get_connection():
#     logger.info("🔌 Attempting to create Snowflake session...")
#     try:
#         session = Session.builder.configs(SNOWFLAKE_CONFIG).create()
#         logger.info("✅ Snowflake session established.")
#         return session
#     except Exception as e:
#         logger.error("❌ Failed to create Snowflake session.")
#         logger.error(f"🔍 Reason: {e}")
#         traceback.print_exc()
#         return None

# # ------------------------------------------------------------------------------
# # ✅ Execute SQL directly — auto manages session like Postgres version
# # ------------------------------------------------------------------------------
# def execute_sql(query):
#     logger.info("📥 Starting execute_sql...")
#     try:
#         session = get_connection()
#         if not session:
#             logger.error("❌ Cannot execute SQL — no connection.")
#             return []

#         logger.info(f"📤 Executing query:\n{query}")
#         result = session.sql(query).collect()
#         session.close()
#         logger.info(f"✅ Query successful. Rows: {len(result)}")
#         return [row.as_dict() for row in result]

#     except Exception as e:
#         logger.error("❌ SQL execution failed.")
#         logger.error(f"🔍 Reason: {e}")
#         traceback.print_exc()
#         return []
