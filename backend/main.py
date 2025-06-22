



# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from sql_mapper import generate_sql_query
# import sqlite3
# from db import execute_sql
# # from sql_mapper import fill_sql_template


# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class QueryRequest(BaseModel):
#     prompt: str

# @app.post("/query")
# async def query(request: QueryRequest):
#     prompt = request.prompt
#     sql = generate_sql_query(prompt)

#     if sql == "UNSUPPORTED":
#         return {"sql": None, "response": "Sorry, I couldn't understand the question."}

#     result = execute_sql(sql)

#     return {
#         "sql": sql.strip(),
#         "response": result if result else "No data found."
#     }

# @app.post("/data")
# async def get_data(request: QueryRequest):
#     prompt = request.prompt
#     sql = generate_sql_query(prompt)

#     if sql == "UNSUPPORTED":
#         print("Prompt unsupported:", prompt)
#         return {
#             "response": "Sorry, I couldn't understand the question.",
#             "sql": None
#         }

#     try:
#         conn = sqlite3.connect("chase_demo.db")
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         result = [dict(row) for row in rows]
#         conn.close()

#         response_data = {
#             "response": result if result else "No data found.",
#             "sql": sql.strip()
#         }

#         print(" Prompt:", prompt)
#         print(" SQL:", sql.strip())
#         print(" Response:", response_data["response"])

#         return response_data

#     except Exception as e:
#         print("❌ SQL Execution Error:", e)
#         raise HTTPException(status_code=500, detail=f"SQL Error: {e}")


# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from sql_mapper import generate_sql_query
# from nlp_utils import extract_intent_and_slots
# import sqlite3
# from db import execute_sql

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class QueryRequest(BaseModel):
#     prompt: str

# @app.post("/query")
# async def query(request: QueryRequest):
#     prompt = request.prompt
#     slots = extract_intent_and_slots(prompt)
#     sql = generate_sql_query(slots)

#     if sql == "UNSUPPORTED":
#         return {"sql": None, "response": "Sorry, I couldn't understand the question."}

#     result = execute_sql(sql)

#     return {
#         "sql": sql.strip(),
#         "response": result if result else "No data found."
#     }

# @app.post("/data")
# async def get_data(request: QueryRequest):
#     prompt = request.prompt
#     slots = extract_intent_and_slots(prompt)

#     if not slots:
#         print("Prompt unsupported:", prompt)
#         return {
#             "response": "Sorry, I couldn't understand the question.",
#             "sql": None
#         }

#     sql = generate_sql_query(slots)

#     try:
#         conn = sqlite3.connect("chase_demo.db")
#         conn.row_factory = sqlite3.Row
#         cursor = conn.cursor()
#         cursor.execute(sql)
#         rows = cursor.fetchall()
#         result = [dict(row) for row in rows]
#         conn.close()

#         response_data = {
#             "response": result if result else "No data found.",
#             "sql": sql.strip()
#         }

#         print(" Prompt:", prompt)
#         print(" SQL:", sql.strip())
#         print(" Response:", response_data["response"])

#         return response_data

#     except Exception as e:
#         print("❌ SQL Execution Error:", e)
#         raise HTTPException(status_code=500, detail=f"SQL Error: {e}")




from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sql_mapper import generate_sql_query
from nlp_utils import extract_intent_and_slots
import sqlite3
from db import execute_sql

app = FastAPI()

# Enable CORS for all origins (can be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    prompt: str

@app.post("/query")
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

@app.post("/data")
async def get_data(request: QueryRequest):
    prompt = request.prompt
    slots = extract_intent_and_slots(prompt)

    if not slots:
        print("❌ Unsupported prompt:", prompt)
        return {
            "response": "Sorry, I couldn't understand the question.",
            "sql": None
        }

    sql = generate_sql_query(slots)

    try:
        conn = sqlite3.connect("chase_demo.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        conn.close()

        response_data = {
            "response": result if result else "No data found.",
            "sql": sql.strip()
        }

        print("  Prompt  :", prompt)
        print("  SQL query  :", sql.strip())
        print("  Response    :", response_data["response"])

        return response_data

    except Exception as e:
        print("❌ SQL Execution Error:", e)
        raise HTTPException(status_code=500, detail=f"SQL Error: {e}")
