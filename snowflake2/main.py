



# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from mapper import generate_sql_query
# from rag_retriever import retrieve_relevant_table, schema_metadata
# from db import execute_sql
# from followup_handler import is_follow_up_prompt, get_followup_query

# import logging

# app = FastAPI()
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("main")

# # ✅ CORS setup
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ In-memory conversation context
# memory_context = []

# @app.post("/data")
# async def get_data(request: Request):
#     body = await request.json()
#     prompt = body.get("prompt")

#     logger.info(f"📨 Prompt received: {prompt}")

#     try:
#         # 🔄 Check if it's a follow-up
#         if is_follow_up_prompt(prompt):
#             logger.info("🔄 Detected follow-up query. Attempting resolution...")
#             sql = get_followup_query(prompt, memory_context)

#             if not sql:
#                 logger.warning("⚠️ Follow-up detected but no valid SQL could be resolved.")
#                 return {"response": "⚠️ Couldn't resolve a valid SQL from previous context.", "data": []}

#             logger.info(f"🧠 Resolved follow-up SQL: {sql}")
#         else:
#             # 🧠 Normal prompt
#             rag_data = retrieve_relevant_table(prompt)
#             logger.info(f"📥 RAG Matches: {rag_data}")

#             matched_table = list(rag_data.keys())[0]
#             matched_metadata = rag_data.get(matched_table)

#             if not matched_metadata or not isinstance(matched_metadata, dict):
#                 raise ValueError("Invalid matched_metadata: None or not a dictionary")

#             sql = generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata)
#             logger.info(f"🧠 SQL Query generated: {sql}")

#         # ✅ Execute SQL
#         result = execute_sql(sql)

#         # 💾 Save to memory
#         # add_to_memory(prompt, sql, result)
#         memory_context.append({"prompt": prompt, "sql": sql})
#         if len(memory_context) > 3:
#             memory_context.pop(0)

#         return {
#             "response": "✅ Query executed successfully.",
#             "data": result,
#             "sql": sql
#         }

#     except Exception as e:
#         logger.error(f"❌ Failed to generate SQL: {e}")
#         return {
#             "response": f"❌ Failed to generate SQL: {str(e)}"
#         }


















# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from mapper import generate_sql_query
# from rag_retriever import retrieve_relevant_table, schema_metadata
# from db import execute_sql
# from followup_handler import is_follow_up_prompt, get_followup_query
# import logging
# import sys

# # Configure logging with console output
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )
# logger = logging.getLogger("main")

# app = FastAPI()

# # CORS setup
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # In-memory conversation context
# memory_context = []

# @app.post("/data")
# async def get_data(request: Request):
#     body = await request.json()
#     prompt = body.get("prompt")

#     logger.info(f"📨 Prompt received: '{prompt}'")
#     logger.debug(f"schema_metadata keys: {list(schema_metadata.keys())}")

#     try:
#         # Check if it's a follow-up
#         logger.debug(f"Checking if prompt is follow-up: '{prompt}'")
#         if is_follow_up_prompt(prompt):
#             logger.info("🔄 Detected follow-up query. Attempting resolution...")
#             sql = get_followup_query(prompt, memory_context)

#             if not sql:
#                 logger.error(f"⚠️ Follow-up query failed: No valid SQL generated. Memory context: {memory_context}")
#                 return {
#                     "response": "⚠️ Unable to process follow-up query. Please specify the application type or provide more context.",
#                     "data": []
#                 }

#             logger.info(f"🧠 Resolved follow-up SQL: '{sql}'")
#         else:
#             # Normal prompt
#             logger.debug("Processing as normal prompt")
#             rag_data = retrieve_relevant_table(prompt)
#             logger.info(f"📥 RAG Matches: {rag_data}")

#             if not rag_data:
#                 logger.error("No relevant table found by RAG retriever")
#                 return {"response": "❌ No relevant table found for the prompt.", "data": []}

#             matched_table = list(rag_data.keys())[0]
#             matched_metadata = rag_data.get(matched_table)

#             if not matched_metadata or not isinstance(matched_metadata, dict):
#                 raise ValueError("Invalid matched_metadata: None or not a dictionary")

#             sql = generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata)
#             logger.info(f"🧠 SQL Query generated: '{sql}'")

#         # Execute SQL
#         result = execute_sql(sql)

#         # Save to memory for normal prompts only
#         if not is_follow_up_prompt(prompt):
#             memory_context.append({
#                 "prompt": prompt,
#                 "sql": sql,
#                 "table_name": matched_table.upper(),
#                 "schema": matched_metadata  # Use RAG metadata directly
#             })
#             if len(memory_context) > 1:
#                 memory_context.pop(0)
#             logger.debug(f"Memory context updated: {memory_context}")

#         return {
#             "response": "✅ Query executed successfully.",
#             "data": result,
#             "sql": sql
#         }

#     except Exception as e:
#         logger.error(f"❌ Failed to generate SQL: {e}")
#         return {
#             "response": f"❌ Failed to generate SQL: {str(e)}",
#             "data": []
#         }
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mapper import generate_sql_query
from rag_retriever import retrieve_relevant_table, schema_metadata
from db import execute_sql
from followup_handler import is_follow_up_prompt, get_followup_query
import logging
import sys
import auto_progress
import json
from mapper import business_terms

# Configure logging with console output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

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
        logger.debug(f"Checking if prompt is follow-up: '{prompt}'")
        if is_follow_up_prompt(prompt):
            logger.info("🔄 Detected follow-up query. Attempting resolution...")
            sql = get_followup_query(prompt, memory_context)

            if not sql:
                logger.error(f"⚠️ Follow-up query failed: No valid SQL generated. Memory context: {memory_context}")
                return {
                    "response": "⚠️ Unable to process follow-up query. Please specify the application type or provide more context.",
                    "data": []
                }

            logger.info(f"🧠 Resolved follow-up SQL: '{sql}'")
        else:
            # Check for auto progress request
            is_progress, table = auto_progress.detect_progress_request(prompt)
            if is_progress:
                logger.info(f"🔄 Detected auto progress request for table: {table}")
                sql = auto_progress.build_progress_query(prompt, schema_metadata, business_terms)
                if not sql:
                    logger.warning("⚠️ Auto progress query generation failed.")
                    return {
                        "response": "⚠️ Failed to generate auto progress query.",
                        "data": []
                    }
                logger.info(f"🧠 Generated auto progress SQL: '{sql}'")

                # Execute SQL to fetch data
                result = execute_sql(sql)
                if not result or not isinstance(result, list):
                    logger.warning("⚠️ No data or invalid data returned from auto progress query.")
                    return {
                        "response": "⚠️ No data available for auto progress.",
                        "data": [],
                        "sql": sql
                    }

                # Process result into a table
                table_data = {}
                for row in result:
                    month = row.get("Month")
                    if month:
                        if month not in table_data:
                            table_data[month] = {}
                        for key, value in row.items():
                            if key != "Month" and value is not None:
                                table_data[month][key] = value

                # Convert to list of dictionaries for JSON
                json_table = [{"Month": month, **metrics} for month, metrics in table_data.items()]
                logger.info(f"🧠 Processed auto progress table: {json_table}")

                return {
                    "response": "✅ Auto progress query executed successfully.",
                    "data": json_table,
                    "sql": sql
                }

            # Normal prompt
            logger.debug("Processing as normal prompt")
            rag_data = retrieve_relevant_table(prompt)
            logger.info(f"📥 RAG Matches: {rag_data}")

            if not rag_data:
                logger.error("No relevant table found by RAG retriever")
                return {"response": "❌ No relevant table found for the prompt.", "data": []}

            matched_table = list(rag_data.keys())[0]
            matched_metadata = rag_data.get(matched_table)

            if not matched_metadata or not isinstance(matched_metadata, dict):
                raise ValueError("Invalid matched_metadata: None or not a dictionary")

            sql = generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata)
            logger.info(f"🧠 SQL Query generated: '{sql}'")

        # Execute SQL for non-progress, non-follow-up prompts
        result = execute_sql(sql)

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
            "response": "✅ Query executed successfully.",
            "data": result,
            "sql": sql
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate SQL: {e}")
        return {
            "response": f"❌ Failed to generate SQL: {str(e)}",
            "data": []
        }