from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sql_mapper import generate_sql_query
from db import execute_sql, setup_database

# Initialize SQLite database from schema
setup_database()

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
    return {"message": "✅ Backend is running with SQLite"}

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
        "sql": sql.strip(),
        "response": result if result else "No data found."
    }
