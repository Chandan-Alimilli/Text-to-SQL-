import os
import logging
import traceback
from snowflake.snowpark import Session

# ------------------------------------------------------------------------------
# ✅ Logging Setup
# ------------------------------------------------------------------------------
logger = logging.getLogger("db")

# ------------------------------------------------------------------------------
# ✅ JPM Proxy Setup (optional - enable if needed)
# ------------------------------------------------------------------------------
USE_JPM_PROXY = True  # Change to False if testing locally

if USE_JPM_PROXY:
    os.environ["HTTPS_PROXY"] = "http://proxy.jpmchase.net:10443"
    os.environ["HTTP_PROXY"] = os.environ["HTTPS_PROXY"]
    os.environ["NO_PROXY"] = "localhost,127.0.0.1,.jpmchase.net,.jpmorganchase.net,.eks.amazonaws.com"

# ------------------------------------------------------------------------------
# ✅ Snowflake Config
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# ✅ Global Session Holder
# ------------------------------------------------------------------------------
snowflake_session = None

def init_connection_once():
    global snowflake_session
    if snowflake_session is None:
        logger.info("🔌 Establishing Snowflake session (first time only)...")
        try:
            snowflake_session = Session.builder.configs(SNOWFLAKE_CONFIG).create()
            logger.info("✅ Snowflake session established successfully.")
        except Exception as e:
            logger.error("❌ Failed to create Snowflake session.")
            logger.error(f"🔍 Reason: {e}")
            traceback.print_exc()
            snowflake_session = None
    return snowflake_session

# ------------------------------------------------------------------------------
# ✅ Execute SQL using persistent session
# ------------------------------------------------------------------------------
def execute_sql(query):
    logger.info("📥 Starting execute_sql...")
    try:
        session = init_connection_once()
        if not session:
            logger.error("❌ Cannot execute SQL — session not initialized.")
            return []

        logger.info(f"📤 Executing query:\n{query}")
        result = session.sql(query).collect()
        logger.info(f"✅ Query successful. Rows: {len(result)}")
        return [row.as_dict() for row in result]

    except Exception as e:
        logger.error("❌ SQL execution failed.")
        logger.error(f"🔍 Reason: {e}")
        traceback.print_exc()
        return []
