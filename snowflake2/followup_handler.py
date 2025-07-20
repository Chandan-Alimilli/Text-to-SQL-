import re
import json

# ✅ Load follow-up rules (keywords, transforms, months)
with open("followup_rules.json", "r") as f:
    FOLLOWUP_RULES = json.load(f)

# ✅ Load business mapping for filters
with open("business_mapping.json", "r") as f:
    BUSINESS_MAPPING = json.load(f)

# ✅ In-memory conversation history
conversation_memory = []
MAX_MEMORY = 3


def is_follow_up_prompt(prompt):
    """
    Check if the prompt contains follow-up indicators.
    """
    prompt_lower = prompt.lower()
    return any(k in prompt_lower for k in FOLLOWUP_RULES["followup_keywords"])


def get_business_conditions_from_prompt(prompt):
    """
    Returns a list of SQL conditions (e.g., APPL_APRV_IN = 1) 
    based on business keywords from the prompt.
    """
    prompt_lower = prompt.lower()
    conditions = []

    for keyword, rule in BUSINESS_MAPPING.items():
        if keyword in prompt_lower:
            column = rule["column"]
            if rule.get("is_null"):
                conditions.append(f"{column} IS NULL")
            elif rule.get("not_null"):
                conditions.append(f"{column} IS NOT NULL")
            else:
                value = rule["value"]
                if isinstance(value, str):
                    conditions.append(f"{column} = '{value}'")
                else:
                    conditions.append(f"{column} = {value}")
    return conditions


def get_followup_query(prompt, memory_context):
    """
    Given a follow-up prompt and memory context, generate the new SQL query.
    """
    prompt_lower = prompt.lower()

    if not is_follow_up_prompt(prompt_lower) or not memory_context:
        return None

    for mem in reversed(memory_context[-MAX_MEMORY:]):
        last_prompt = mem["prompt"].lower()
        last_sql = mem["sql"]

        new_sql = last_sql

        # 🔁 COUNT → SELECT *
        for trigger in FOLLOWUP_RULES["transforms"]["count_to_detail"]["trigger_patterns"]:
            if trigger in last_prompt and "count" not in prompt_lower:
                pattern = FOLLOWUP_RULES["transforms"]["count_to_detail"]["replacement"]["regex"]
                repl = FOLLOWUP_RULES["transforms"]["count_to_detail"]["replacement"]["replace_with"]
                new_sql = re.sub(pattern, repl, new_sql, flags=re.IGNORECASE)

        # 📅 Add month filter (e.g., "only June")
        for month, num in FOLLOWUP_RULES["month_filters"].items():
            if month in prompt_lower:
                condition = f"EXTRACT(MONTH FROM appl_init_dt) = {num}"
                if "WHERE" in new_sql.upper():
                    new_sql += f" AND {condition}"
                else:
                    new_sql += f" WHERE {condition}"

        # 🏷️ Add business filters (e.g., "only approved")
        business_conditions = get_business_conditions_from_prompt(prompt)
        if business_conditions:
            condition_str = " AND ".join(business_conditions)
            if "WHERE" in new_sql.upper():
                new_sql += f" AND {condition_str}"
            else:
                new_sql += f" WHERE {condition_str}"

               # ✅ Fix misplaced LIMIT clause
        if "LIMIT" in new_sql.upper():
            limit_match = re.search(r"\s+LIMIT\s+\d+", new_sql, flags=re.IGNORECASE)
            if limit_match:
                limit_clause = limit_match.group()
                new_sql = re.sub(r"\s+LIMIT\s+\d+", "", new_sql, flags=re.IGNORECASE).strip()
                new_sql += f" {limit_clause}"

        if new_sql != last_sql:
            return new_sql


    return None


def add_to_memory(prompt, sql, response):
    """
    Store conversation memory for follow-up handling.
    """
    conversation_memory.append({
        "prompt": prompt,
        "sql": sql,
        "response": response
    })
    if len(conversation_memory) > MAX_MEMORY:
        conversation_memory.pop(0)  # keep last 3 only
