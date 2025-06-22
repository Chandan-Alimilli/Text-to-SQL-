

# import spacy

# nlp = spacy.load("en_core_web_sm")

# def extract_intent_and_slots(prompt: str):
#     doc = nlp(prompt)
#     slots = {}
#     intent = None

#     # Lowercased lemmas of all tokens
#     lemmas = [token.lemma_.lower() for token in doc]
#     nouns = [token.text.lower() for token in doc if token.pos_ == "NOUN"]

#     # Intent detection
#     if "list" in lemmas or "show" in lemmas:
#         if "branch" in nouns:
#             intent = "list_branches"
#         elif "customer" in nouns:
#             intent = "list_customers"
#         elif "transaction" in nouns:
#             intent = "transactions_with_customers"

#     elif "number" in lemmas or "count" in lemmas:
#         if "branch" in nouns:
#             intent = "count_branches"
#         elif "customer" in nouns and "branch" in nouns:
#             intent = "customers_by_branch"
#         elif "transaction" in nouns and "category" in nouns:
#             intent = "transactions_per_category"

#     elif "total" in lemmas or "sum" in lemmas:
#         if "revenue" in nouns:
#             intent = "branch_revenue"
#         elif "spend" in lemmas or "amount" in nouns and "customer" in nouns:
#             intent = "customer_spend_total"
#         elif "transaction" in nouns and "category" in nouns:
#             intent = "transactions_per_category"

#     elif "average" in lemmas and "staff" in nouns:
#         intent = "average_staff"

#     elif "most" in lemmas or "highest" in lemmas:
#         if "revenue" in nouns and "branch" in nouns:
#             intent = "most_revenue_branch"
#         elif "customer" in nouns and "spend" in lemmas:
#             intent = "top_spender"
#         elif "customer" in nouns and "new" in lemmas:
#             intent = "most_new_customers"
#         elif "transaction" in nouns and "category" in nouns:
#             intent = "top_transaction_category"

#     elif "per" in lemmas and "day" in nouns:
#         intent = "transactions_per_day"

#     # Final decision
#     if intent:
#         slots["intent"] = intent
#         return slots

#     return None





from typing import Dict
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_lemmas(prompt: str):
    doc = nlp(prompt)
    return [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]

def extract_intent_and_slots(prompt: str) -> Dict:
    return {"prompt": prompt}  # simple wrapper to keep compatibility

