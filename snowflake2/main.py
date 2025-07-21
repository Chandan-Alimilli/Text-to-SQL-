



from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mapper import generate_sql_query
from rag_retriever import retrieve_relevant_table, schema_metadata
from db import execute_sql
from followup_handler import is_follow_up_prompt, get_followup_query, add_to_memory

import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ✅ CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ In-memory conversation context
memory_context = []

@app.post("/data")
async def get_data(request: Request):
    body = await request.json()
    prompt = body.get("prompt")

    logger.info(f"📨 Prompt received: {prompt}")

    try:
        # 🔄 Check if it's a follow-up
        if is_follow_up_prompt(prompt):
            logger.info("🔄 Detected follow-up query. Attempting resolution...")
            sql = get_followup_query(prompt, memory_context)

            if not sql:
                logger.warning("⚠️ Follow-up detected but no valid SQL could be resolved.")
                return {"response": "⚠️ Couldn't resolve a valid SQL from previous context.", "data": []}

            logger.info(f"🧠 Resolved follow-up SQL: {sql}")
        else:
            # 🧠 Normal prompt
            rag_data = retrieve_relevant_table(prompt)
            logger.info(f"📥 RAG Matches: {rag_data}")

            matched_table = list(rag_data.keys())[0]
            matched_metadata = rag_data.get(matched_table)

            if not matched_metadata or not isinstance(matched_metadata, dict):
                raise ValueError("Invalid matched_metadata: None or not a dictionary")

            sql = generate_sql_query(prompt, matched_table, matched_metadata, rag_data, schema_metadata)
            logger.info(f"🧠 SQL Query generated: {sql}")

        # ✅ Execute SQL
        result = execute_sql(sql)

        # 💾 Save to memory
        add_to_memory(prompt, sql, result)
        memory_context.append({"prompt": prompt, "sql": sql})
        if len(memory_context) > 3:
            memory_context.pop(0)

        return {
            "response": "✅ Query executed successfully.",
            "data": result,
            "sql": sql
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate SQL: {e}")
        return {
            "response": f"❌ Failed to generate SQL: {str(e)}"
        }
