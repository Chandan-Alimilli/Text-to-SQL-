import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import get_connection, execute_sql
from mapper import generate_sql_query, summarize_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    try:
        conn = get_connection()
        if conn:
            logging.info("✅ Snowflake connection established")
            # ❌ DO NOT CLOSE the session here
        else:
            logging.warning("⚠️ Snowflake connection failed on startup")
    except Exception as e:
        logging.error(f"❌ Startup error: {e}")

class QueryRequest(BaseModel):
    prompt: str



@app.post("/data")
async def get_data(req: QueryRequest):
    print("📨 Prompt received:", req.prompt)

    sql_query = generate_sql_query({"prompt": req.prompt})
    print("🧠 SQL Query generated:", sql_query)

    if not sql_query or not sql_query.strip().lower().startswith("select"):
        print("❌ No SQL generated.")
        return {"response": "❌ No SQL query generated.", "data": [], "sql": ""}

    result = execute_sql(sql_query)
    response = summarize_response(req.prompt, result)

    # ✅ Print result and summary in terminal
    print("📦 SQL Result:", result)
    print("📝 Summary:", response)

    return {"response": response, "data": result, "sql": sql_query}
