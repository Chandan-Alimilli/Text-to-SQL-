from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from mapper import generate_sql_query
from rag_retriever import retrieve_relevant_table
from db import execute_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "SQL Agent is running."}

@app.post("/data")
async def query_data(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    from_date = body.get("from_date", None)
    to_date = body.get("to_date", None)
    limit = body.get("record_limit", body.get("limit", 25))

    logger.info(f"📨 Prompt received: {prompt}")

    matched_table = retrieve_relevant_table(prompt)
    logger.info(f"📥 RAG Matches: {matched_table}")

    if not matched_table:
        return {"response": "❌ No relevant table found.", "data": [], "sql": ""}

    try:
        sql_query = generate_sql_query(prompt, matched_table, from_date, to_date, limit)
        logger.info(f"🧠 SQL Query generated: {sql_query}")
    except Exception as e:
        logger.error(f"❌ Failed to generate SQL: {e}")
        return {"response": f"❌ Failed to generate SQL: {e}", "data": [], "sql": ""}

    try:
        result = execute_query(sql_query)
        return {
            "response": "✅ Query executed successfully.",
            "data": result,
            "sql": sql_query
        }
    except Exception as e:
        logger.error(f"❌ Error executing query: {e}")
        return {
            "response": f"❌ Error executing query: {e}",
            "data": [],
            "sql": sql_query
        }
