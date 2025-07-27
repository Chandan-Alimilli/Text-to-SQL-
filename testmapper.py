import snowflake.connector
from snowflake.connector import DictCursor
import logging
import time
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Snowflake configuration (REPLACE THESE WITH YOUR ACTUAL CREDENTIALS)
SNOWFLAKE_CONFIG = {
    "account": "your_account",  # e.g., "xy12345.ap-southeast-1" (replace with your Snowflake account identifier)
    "user": "your_username",    # Replace with your Snowflake username
    "password": "your_password", # Replace with your Snowflake password
    "warehouse": "your_warehouse", # Replace with your warehouse name (e.g., "COMPUTE_WH")
    "database": "your_database",  # Replace with your database name (e.g., "MY_DB")
    "schema": "your_schema",     # Replace with your schema name (e.g., "PUBLIC")
    "role": "your_role",        # Optional: Replace with your role (e.g., "SYSADMIN") if required
    "timezone": "Asia/Kolkata"  # Matches current IST (01:51 AM)
}

global_session = None

def get_connection():
    global global_session
    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            if not global_session or not global_session.is_still_alive():
                logger.debug(f"Attempt {attempt + 1}/{max_retries}: Creating new Snowflake session...")
                global_session = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
                logger.info("✅ Snowflake session established successfully.")
            else:
                # Validate session with a lightweight query
                with global_session.cursor() as cursor:
                    cursor.execute("SELECT CURRENT_TIMESTAMP")
                    cursor.fetchone()
                logger.debug("Session validated.")

            return global_session

        except snowflake.connector.errors.Error as e:
            logger.error(f"❌ Snowflake connection failed (Attempt {attempt + 1}): {str(e)}")
            if global_session:
                global_session.close()
            global_session = None
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to connect after {max_retries} attempts: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            if global_session:
                global_session.close()
            global_session = None
            raise

def execute_sql(sql):
    global global_session
    try:
        session = get_connection()
        if not session:
            raise Exception("No active Snowflake session available.")

        with session.cursor(DictCursor) as cursor:
            logger.debug(f"Executing SQL: {sql}")
            cursor.execute(sql)
            result = cursor.fetchall()
            logger.info("✅ Query executed successfully.")
            return result

    except Exception as e:
        logger.error(f"❌ SQL execution failed: {str(e)}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()

# Example usage
if __name__ == "__main__":
    try:
        # Replace this with your actual query
        result = execute_sql("SELECT 1")
        print(result)
    except Exception as e:
        print(f"Error: {e}")