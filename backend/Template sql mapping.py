

from typing import Dict
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_lemmas(prompt: str):
    doc = nlp(prompt)
    return [token.lemma_.lower() for token in doc if not token.is_stop and token.is_alpha]

def extract_intent_and_slots(prompt: str) -> Dict:
    return {"prompt": prompt}  # simple wrapper to keep compatibility




SQL_TEMPLATES = {
    "total_customers": "SELECT COUNT(*) as total_customers FROM customers;",
    "all_customers": "SELECT * FROM customers;",
    "customers_with_emails": """SELECT c.name as customer_name, c.email, b.name as branch_name, b.location 
                                FROM customers c JOIN branches b ON c.branch_id = b.id;""",
    "revenue_by_branch": """SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue 
                            FROM performance p JOIN branches b ON p.branch_id = b.id 
                            GROUP BY p.branch_id;""",
    "avg_staff": """SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff 
                    FROM performance p JOIN branches b ON p.branch_id = b.id 
                    GROUP BY p.branch_id;""",
    "transactions_per_category": """SELECT category, COUNT(*) as count, SUM(amount) as total_amount 
                                    FROM transactions GROUP BY category;""",
    "highest_transaction": """SELECT c.name AS customer_name, t.amount, t.date, t.category 
                              FROM transactions t JOIN customers c ON t.customer_id = c.id 
                              ORDER BY t.amount DESC LIMIT 1;""",
    "total_spent_by_customer": """SELECT c.name AS customer_name, SUM(t.amount) AS total_spent 
                                  FROM customers c JOIN transactions t ON c.id = t.customer_id 
                                  GROUP BY c.id;""",
    "branch_locations": "SELECT DISTINCT location FROM branches;",
    "total_branches": "SELECT COUNT(*) AS total_branches FROM branches;",
    "top_branch_new_customers": """SELECT b.name AS branch_name, SUM(p.number_of_new_customers) AS total_new_customers 
                                   FROM performance p JOIN branches b ON p.branch_id = b.id 
                                   GROUP BY b.id ORDER BY total_new_customers DESC LIMIT 1;""",
    "top_customer_spent": """SELECT c.name AS customer_name, SUM(t.amount) AS total_spent 
                             FROM customers c JOIN transactions t ON c.id = t.customer_id 
                             GROUP BY c.id ORDER BY total_spent DESC LIMIT 1;"""
}

INTENT_KEYWORDS = {
    "total_customers": ["total", "number", "count", "customer"],
    "all_customers": ["all", "list", "show", "customer", "table", "name"],
    "customers_with_emails": ["email", "customer", "contact"],
    "revenue_by_branch": ["revenue", "branch"],
    "avg_staff": ["average", "staff", "employee"],
    "transactions_per_category": ["transaction", "category", "group"],
    "highest_transaction": ["highest", "largest", "biggest", "transaction"],
    "total_spent_by_customer": ["spend", "total", "customer"],
    "branch_locations": ["branch", "location"],
    "total_branches": ["total", "number", "branch"],
    "top_branch_new_customers": ["most", "new", "customer", "branch"],
    "top_customer_spent": ["customer", "spend", "most", "top"]
}


def detect_intent(prompt: str):
    lemmas = extract_lemmas(prompt)
    best_intent = None
    best_score = 0

    for intent, keywords in INTENT_KEYWORDS.items():
        matched = sum(1 for kw in keywords if kw in lemmas)
        score = matched / len(keywords)  # Normalize by keyword list length

        if score > best_score:
            best_score = score
            best_intent = intent

    # Only return intent if there’s a meaningful match
    if best_score >= 0.4:  # you can fine-tune this threshold
        return best_intent
    return None


def generate_sql_query(slots: dict):
    prompt = slots.get("prompt", "")
    intent = detect_intent(prompt)
    print(f"Detected intent: {intent}")
    if intent and intent in SQL_TEMPLATES:
        return SQL_TEMPLATES[intent]
    return "UNSUPPORTED"

