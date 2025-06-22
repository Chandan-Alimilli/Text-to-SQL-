from nlp_utils import extract_lemmas

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




# def generate_sql_query(slots):
#     intent = slots.get("intent")

#     if intent == "list_branches":
#         return "SELECT id, name, location FROM branches;"

#     elif intent == "count_branches":
#         return "SELECT COUNT(*) AS total_branches FROM branches;"

#     elif intent == "branch_revenue":
#         return """
#         SELECT b.name AS branch_name, SUM(p.revenue_generated) AS total_revenue
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY b.name;
#         """

#     elif intent == "total_revenue_all_branches":
#         return """
#         SELECT SUM(p.revenue_generated) AS total_revenue
#         FROM performance p;
#         """

#     elif intent == "average_staff":
#         return """
#         SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY b.name;
#         """

#     elif intent == "list_customers":
#         return "SELECT id, name, email FROM customers;"

#     elif intent == "customers_with_branch_info":
#         return """
#         SELECT c.id, c.name, c.email, b.name AS branch_name, b.location
#         FROM customers c
#         JOIN branches b ON c.branch_id = b.id;
#         """

#     elif intent == "customer_spend_total":
#         return """
#         SELECT c.name AS label, SUM(t.amount) AS value
#         FROM transactions t
#         JOIN customers c ON t.customer_id = c.id
#         GROUP BY c.name
#         ORDER BY value DESC;
#         """

#     elif intent == "top_spender":
#         return """
#         SELECT c.name, SUM(t.amount) AS total_spent
#         FROM transactions t
#         JOIN customers c ON t.customer_id = c.id
#         GROUP BY c.name
#         ORDER BY total_spent DESC
#         LIMIT 1;
#         """

#     elif intent == "top_transaction_customer":
#         return """
#         SELECT c.name, MAX(t.amount) AS highest_transaction
#         FROM transactions t
#         JOIN customers c ON t.customer_id = c.id;
#         """

#     elif intent == "customers_by_branch":
#         return """
#         SELECT b.name AS branch_name, COUNT(c.id) AS customer_count
#         FROM customers c
#         JOIN branches b ON c.branch_id = b.id
#         GROUP BY b.name;
#         """

#     elif intent == "transactions_with_customers":
#         return """
#         SELECT t.id, t.amount, t.date, c.name, c.email
#         FROM transactions t
#         JOIN customers c ON t.customer_id = c.id;
#         """

#     elif intent == "transactions_per_category":
#         return """
#         SELECT category, COUNT(*) AS count
#         FROM transactions
#         GROUP BY category;
#         """

#     elif intent == "top_transaction_category":
#         return """
#         SELECT category, SUM(amount) AS total_value
#         FROM transactions
#         GROUP BY category
#         ORDER BY total_value DESC
#         LIMIT 1;
#         """

#     elif intent == "most_revenue_branch":
#         return """
#         SELECT b.name, SUM(p.revenue_generated) AS total_revenue
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY b.name
#         ORDER BY total_revenue DESC
#         LIMIT 1;
#         """

#     elif intent == "most_new_customers":
#         return """
#         SELECT b.name, MAX(p.number_of_new_customers) AS new_customers
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY b.name
#         ORDER BY new_customers DESC
#         LIMIT 1;
#         """

#     elif intent == "transactions_per_day":
#         return """
#         SELECT date, SUM(amount) AS total
#         FROM transactions
#         GROUP BY date
#         ORDER BY date ASC;
#         """

#     return "UNSUPPORTED"