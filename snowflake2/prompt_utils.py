import re

def extract_limit_from_prompt(prompt, default_limit=50):
    prompt = prompt.lower()

    # Matches: "limit 10", "limit of 10", "show 25 rows", "fetch 50 records", etc.
    match = re.search(r"(?:limit(?:\s+of)?|show|fetch)?\s*(\d+)\s*(?:records|rows)?", prompt)

    if match:
        try:
            return int(match.group(1))
        except:
            return default_limit
    return default_limit
