# main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mapper import generate_sql_query, summarize_response
from db import execute_sql
import logging

# 🌐 Enable logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 🌍 CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📦 Request model
class QueryRequest(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"message": "✅ Snowflake NLP Agent is running!"}


@app.post("/data")
async def get_data(req: QueryRequest):
    sql = generate_sql_query({"prompt": req.prompt})
    result = execute_sql(sql)
    response_text = summarize_response(req.prompt, result)
    return {
        "response": response_text,
        "data": result,
        "sql": sql
    }
