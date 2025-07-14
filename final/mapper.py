import spacy
import re
from rag_retriever import get_schema_matches

nlp = spacy.load("en_core_web_sm")

def extract_intents_and_entities(prompt: str):
    doc = nlp(prompt)
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    nouns = [chunk.text.lower() for chunk in doc.noun_chunks]
    dates = [ent.text for ent in doc.ents if ent.label_ in ("DATE", "TIME")]

    return {
        "verbs": verbs,
        "nouns": nouns,
        "dates": dates
    }

def generate_sql(prompt: str):
    schema_matches = get_schema_matches(prompt)
    if not schema_matches:
        return ""

    intents = extract_intents_and_entities(prompt)

    queries = []
    for table, columns in schema_matches.items():
        if not columns:
            continue

        select_cols = ", ".join(columns[:5])
        query = f"SELECT {select_cols} FROM {table}"

        if intents["dates"]:
            for date_str in intents["dates"]:
                if re.search(r"\d{4}-\d{2}", date_str):
                    query += f" WHERE SNPST_DT LIKE '{date_str}%'"
                    break
                elif "june" in date_str.lower():
                    query += f" WHERE SNPST_DT LIKE '%-06-%'"
                    break

        query += " LIMIT 10"
        queries.append(query)

    return "; ".join(queries)
