# snowflake_main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from snowflake_mapper import generate_sql_query
from snowflake_db import execute_sql

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "✅ Snowflake NLP Agent is running"}

class QueryRequest(BaseModel):
    prompt: str

@app.post("/data")
async def query(request: QueryRequest):
    prompt = request.prompt
    slots = { "prompt": prompt }
    sql = generate_sql_query(slots)

    if sql == "UNSUPPORTED":
        return {
            "sql": None,
            "response": "Sorry, I couldn't understand the question."
        }

    result = execute_sql(sql)
    return {
        "sql": sql,
        "response": result if result else "No data found."
    }

