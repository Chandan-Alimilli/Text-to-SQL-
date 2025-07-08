# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db import execute_sql
from mapper import generate_sql_query, summarize_response
import logging

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    prompt: str

@app.post("/query")
async def query_sql(req: QueryRequest):
    sql_query = generate_sql_query(req.prompt)
    return {"sql": sql_query}

@app.post("/data")
async def get_data(req: QueryRequest):
    sql_query = generate_sql_query(req.prompt)
    print("Generated SQL:", sql_query)
    if not sql_query:
        return {"response": "❌ No SQL query was generated.", "data": [], "sql": ""}
    result = execute_sql(sql_query)
    print("Query Result:", result)
    response_text = summarize_response(req.prompt, result)
    return {"response": response_text, "data": result, "sql": sql_query}