from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mapper import generate_sql
from db import run_query
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/data")
async def get_data(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")

    logging.info(f"📨 Prompt received: {prompt}")
    sql_query = generate_sql(prompt)
    if not sql_query:
        return {"response": "❌ No SQL query generated.", "data": [], "sql": ""}

    data = run_query(sql_query)
    return {"response": "✅ Success", "data": data, "sql": sql_query}
