
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sql_mapper import generate_sql_query
from nlp_utils import extract_intent_and_slots
import sqlite3
from db import execute_sql
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/")
def root():
    return {"message": "✅ Backend is running"}

# Request schema
class QueryRequest(BaseModel):
    prompt: str

# Actual SQL execution and return
@app.post("/data")
async def query(request: QueryRequest):
    prompt = request.prompt
    slots = extract_intent_and_slots(prompt)
    sql = generate_sql_query(slots)

    if sql == "UNSUPPORTED":
        return {"sql": None, "response": "Sorry, I couldn't understand the question."}

    result = execute_sql(sql)

    return {
        "sql": sql.strip(),
        "response": result if result else "No data found."
    }

# Just generate SQL (dry-run)
@app.post("/query")
async def get_data(request: QueryRequest):
    prompt = request.prompt
    slots = extract_intent_and_slots(prompt)

    if not slots:
        print("❌ Unsupported prompt:", prompt)
        return {
            "sql": None,
            "response": "Sorry, I couldn't understand the question."
        }

    sql = generate_sql_query(slots)

    if sql == "UNSUPPORTED":
        print("❌ Unsupported SQL generation for prompt:", prompt)
        return {
            "sql": None,
            "response": "Sorry, I couldn't generate a SQL query for your question."
        }

    print("  Prompt  :", prompt)
    print("  SQL query  :", sql.strip())

    return {
        "sql": sql.strip(),
        "response": "SQL query generated successfully."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

