



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sql_mapper import generate_sql_query
from db import execute_sql

app = FastAPI()

# Enable CORS for all origins (adjust for production if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Endpoint: Get SQL + Data
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

# Endpoint: Just get SQL (dry run)
@app.post("/query")
async def get_data(request: QueryRequest):
    prompt = request.prompt
    slots = { "prompt": prompt } 
    sql = generate_sql_query(slots)

    if sql == "UNSUPPORTED":
        return {
            "sql": None,
            "response": "Sorry, I couldn't generate a SQL query for your question."
        }

    return {
        "sql": sql.strip(),
        "response": "SQL query generated successfully."
    }

# Optional: for running locally
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
