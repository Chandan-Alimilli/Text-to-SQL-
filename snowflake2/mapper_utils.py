import re
import json
import spacy
import dateparser
from datetime import datetime
from dateutil import parser

nlp = spacy.load("en_core_web_sm")

# ✅ Load business mappings
with open("business_mapping.json", "r") as f:
    BUSINESS_TERMS = json.load(f)


# ✅ Extract noun phrases from prompt
def extract_entities(prompt: str) -> list:
    doc = nlp(prompt)
    return [chunk.text.lower() for chunk in doc.noun_chunks]


# ✅ Parse any date ranges from prompt
def parse_date_range_from_prompt(prompt: str):
    prompt = prompt.lower()
    from_dt, to_dt = None, None

    # Date patterns: yyyy-mm-dd
    date_matches = re.findall(r"\d{4}-\d{2}-\d{1,2}", prompt)
    if len(date_matches) == 1:
        from_dt = to_dt = parser.parse(date_matches[0]).strftime("%Y-%m-%d")
    elif len(date_matches) >= 2:
        from_dt = parser.parse(date_matches[0]).strftime("%Y-%m-%d")
        to_dt = parser.parse(date_matches[1]).strftime("%Y-%m-%d")
    elif any(k in prompt for k in ["last", "this", "next", "month", "week", "year", "today", "yesterday"]):
        parsed = dateparser.parse(prompt)
        if parsed:
            from_dt = to_dt = parsed.strftime("%Y-%m-%d")

    # Check for month names like "in May"
    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    for i, m in enumerate(months):
        if f"in {m}" in prompt or f"month of {m}" in prompt:
            year = datetime.now().year
            from_dt = f"{year}-{i+1:02d}-01"
            to_dt = f"{year}-{i+1:02d}-28"
        elif f"from {m}" in prompt:
            from_dt = f"{datetime.now().year}-{i+1:02d}-01"
        elif f"to {m}" in prompt:
            to_dt = f"{datetime.now().year}-{i+1:02d}-28"

    return from_dt, to_dt


# ✅ Extract comparisons like "term in months < 30", "loan amount > 50000"
def extract_comparative_filters(prompt: str, metadata_columns: dict) -> list:
    filters = []
    prompt_lower = prompt.lower()

    comparison_ops = {
        "less than or equal to": "<=",
        "greater than or equal to": ">=",
        "less than": "<",
        "more than": ">",
        "greater than": ">",
        "equal to": "=",
        "equals": "=",
        "=": "=",
        ">": ">",
        "<": "<",
        ">=": ">=",
        "<=": "<="
    }

    for col, desc in metadata_columns.items():
        col_lower = col.lower()
        desc_lower = desc.lower()

        for phrase, symbol in comparison_ops.items():
            pattern = rf"(?:{desc_lower}|{col_lower})\s+{phrase}\s+([a-zA-Z0-9\-'.]+)"
            match = re.search(pattern, prompt_lower)
            if match:
                value = match.group(1)
                value = f"'{value}'" if not value.replace('.', '').isdigit() else value
                filters.append(f"{col.upper()} {symbol} {value}")

    return filters


# ✅ Extract simple equalities like "state code is NY", "member id 123"
def extract_direct_column_filters(prompt: str, metadata_columns: dict) -> list:
    filters = []
    prompt_lower = prompt

    for col, desc in metadata_columns.items():
        col_lower = col
        desc_lower = desc

        # Accept matches like "state code NY", "member id 123"
        pattern = rf"(?:{desc_lower}|{col_lower})\s+(?:is\s+)?([a-zA-Z0-9\-'.]+)"
        matches = re.findall(pattern, prompt_lower)
        for match in matches:
            value = match.strip()
            value = f"'{value}'" if not value.replace('.', '').isdigit() else value
            filters.append(f"{col.upper()} = {value}")

    return filters
