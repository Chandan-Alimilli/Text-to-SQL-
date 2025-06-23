



from typing import Dict
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_lemmas(prompt: str):
    doc = nlp(prompt)
    return [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]

def extract_intent_and_slots(prompt: str) -> Dict:
    return {"prompt": prompt}  # simple wrapper to keep compatibility

