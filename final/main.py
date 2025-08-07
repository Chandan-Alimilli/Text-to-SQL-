
import logging
import sys
import importlib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mapper import generate_sql_query, business_terms
from rag_retriever import retrieve_relevant_table, schema_metadata
from db import execute_sql
from followup_handler import is_follow_up_prompt, get_followup_query
import auto_progress
import json
from summary_utils import generate_summary_from_result  # Import summary function

# Configure logging with console output and file handler for persistence
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app_debug.log")  # Logs to file for server-side review
    ]
)
logger = logging.getLogger("main")

# Attempt to import modules with error handling
try:
    logger.info("🔄 Initializing module imports...")
    for module in ['mapper', 'rag_retriever', 'db', 'followup_handler', 'auto_progress', 'summary_utils']:
        importlib.import_module(module)
        logger.info(f"✅ Successfully imported module: {module}")
except ImportError as e:
    logger.error(f"❌ Import error occurred: {e}")
    raise
except Exception as e:
    logger.error(f"❌ Unexpected error during import: {e}")
    raise

# Initialize database connection and log status
try:
    logger.info("🔗 Attempting to establish database connection...")
    # Test connection with a simple query
    test_result = execute_sql("SELECT 1")
    if test_result and isinstance(test_result, list):
        logger.info("✅ Database connection established successfully.")
    else:
        logger.warning("⚠️ Database connection test returned unexpected result: {test_result}")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    raise

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation context
memory_context = []

@app.post("/data")
async def get_data(request: Request):
    body = await request.json()
    prompt = body.get("prompt")

    logger.info(f"📨 Prompt received: '{prompt}'")
    logger.debug(f"schema_metadata keys: {list(schema_metadata.keys())}")

    try:
        # Check if it's a follow-up
        logger.debug(f"🔍 Checking if prompt is follow-up: '{prompt}'")
        if is_follow_up_prompt(prompt):
            logger.info("🔄 Detected follow-up query. Attempting resolution...")
            sql = get_followup_query(prompt, memory_context)

            if not sql:
                logger.error(f"⚠️ Follow-up query failed: No valid SQL generated. Memory context: {memory_context}")
                return {
                    "response": "⚠️ Unable to process follow-up query. Please specify the application type or provide more context.",
                    "data": [],
                    "summary": "No summary available due to invalid follow-up query."
                }

            logger.info(f"Resolved follow-up SQL: '{sql}'")
        else:
            # Check for auto progress request
            is_progress, table = auto_progress.detect_progress_request(prompt)
            if is_progress:
                logger.info(f"🔄 Detected auto progress request for table: {table}")
                progress_query = auto_progress.build_progress_query(prompt, schema_metadata, business_terms)
                if not progress_query or not progress_query.get("sql"):
                    logger.warning("⚠️ Auto progress query generation failed.")
                    return {
                        "response": "⚠️ Failed to generate auto progress query.",
                        "data": [],
                        "summary": "No summary available due to failed query generation."
                    }
                sql = progress_query["sql"]
                logger.info(f"Generated auto progress SQL: '{sql}'")

                # Execute SQL to fetch data
                logger.debug(f"Executing auto progress SQL: '{sql}'")
                result = execute_sql(sql)
                if not result or not isinstance(result, list) or len(result) == 0:
                    logger.warning(f"⚠️ No data returned from auto progress query. Result: {result}")
                    return {
                        "response": "⚠️ No data available for the specified period. Please check the date range or table data.",
                        "data": progress_query.get("zero_results", []),
                        "sql": sql,
                        "summary": "No summary available due to no data returned."
                    }

                # Process result into a table
                table_data = {}
                for row in result:
                    logger.debug(f"Processing row: {row}")
                    month = row.get("month")  # Use lowercase 'month' to match SQL alias
                    if month:
                        if month not in table_data:
                            table_data[month] = {}
                        for key, value in row.items():
                            # Handle typos and case sensitivity
                            corrected_key = key.lower()
                            if corrected_key == "booked_appps":
                                corrected_key = "booked_apps"
                            if corrected_key != "month" and value is not None:
                                table_data[month][corrected_key] = value
                    else:
                        logger.warning(f"⚠️ Row missing 'month' key: {row}")

                # Convert to list of dictionaries for JSON
                json_table = [{"month": month, **metrics} for month, metrics in table_data.items()]
                if not json_table:
                    logger.warning("⚠️ Processed table is empty after processing results.")
                    return {
                        "response": "⚠️ No valid data processed for the specified period.",
                        "data": progress_query.get("zero_results", []),
                        "sql": sql,
                        "summary": "No summary available due to empty processed data."
                    }
                logger.info(f"Processed auto progress table: {json_table}")

                return {
                    "response": "Auto progress query executed successfully.",
                    "data": json_table,
                    "sql": sql,
                    "summary": "Auto progress summary not implemented yet."  # Placeholder for future implementation
                }

            # Normal prompt
            logger.debug("🔍 Processing as normal prompt")
            rag_data = retrieve_relevant_table(prompt)
            logger.info(f"RAG Matches: {rag_data}")

            if not rag_data:
                logger.error("❌ No relevant table found by RAG retriever")
                return {
                    "response": "❌ No relevant table found for the prompt.",
                    "data": [],
                    "summary": "No summary available due to no relevant table found."
                }

            matched_table = list(rag_data.keys())[0]
            matched_metadata = rag_data.get(matched_table)

            if not matched_metadata or not isinstance(matched_metadata, dict):
                logger.error("❌ Invalid matched_metadata: None or not a dictionary")
                raise ValueError("Invalid matched_metadata: None or not a dictionary")

            sql = generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata)
            logger.info(f"🧠 SQL Query generated: '{sql}'")

        # Execute SQL for non-progress, non-follow-up prompts
        logger.debug(f"Executing SQL: '{sql}'")
        result = execute_sql(sql)

        # Generate summary for normal and follow-up prompts
        summary = ""
        if not is_progress:  # Exclude auto-progress queries for now
            try:
                # For follow-up, use the table name from memory_context if available
                table_name = matched_table.upper() if not is_follow_up_prompt(prompt) else memory_context[-1].get("table_name", matched_table.upper())
                summary = generate_summary_from_result(result, prompt, sql, table_name)
                logger.info(f"📝 Summary generated: {summary}")
            except Exception as e:
                logger.error(f"⚠️ Failed to generate summary: {e}")
                summary = f"Error generating summary: {str(e)}"

        # Save to memory for normal prompts only
        if not is_follow_up_prompt(prompt) and not is_progress:
            memory_context.append({
                "prompt": prompt,
                "sql": sql,
                "table_name": matched_table.upper(),
                "schema": matched_metadata  # Use RAG metadata directly
            })
            if len(memory_context) > 1:
                memory_context.pop(0)
            logger.debug(f"Memory context updated: {memory_context}")

        return {
            "response": "Query executed successfully.",
            "data": result,
            "sql": sql,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"❌ Failed to process request: {e}", exc_info=True)
        return {
            "response": f"❌ Failed to process request: {str(e)}",
            "data": [],
            "summary": f"Error generating summary: {str(e)}"
        }

if __name__ == "__main__":
    logger.info("🚀 Starting application...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)