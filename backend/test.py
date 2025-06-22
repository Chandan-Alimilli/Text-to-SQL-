



## hardcoded model 

# def generate_sql_query(prompt: str) -> str:
#     import re
#     import nltk
#     from nltk.tokenize import word_tokenize
#     from nltk import pos_tag, ne_chunk
#     from nltk.tree import Tree

#     prompt_lower = prompt.lower()

#     if "total number of branches" in prompt_lower:
#         return "SELECT COUNT(*) as total_branches FROM branches;"

#     if "total revenue" in prompt_lower and "branch" in prompt_lower:
#         return '''
#             SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id;
#         '''

#     if "highest number of new customers" in prompt_lower:
#         return '''
#             SELECT b.name AS branch_name, SUM(p.new_customers) AS new_customers
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id
#             ORDER BY new_customers DESC
#             LIMIT 1;
#         '''

#     if "average staff count" in prompt_lower:
#         return '''
#             SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id;
#         '''

#     if "branch locations" in prompt_lower or "list all branches" in prompt_lower or "show all branches" in prompt_lower:
#         return "SELECT name, location FROM branches;"

#     if "list all customers" in prompt_lower or "show all customers" in prompt_lower:
#         return "SELECT * FROM customers;"

#     if "total count of customers" in prompt_lower or "how many customers" in prompt_lower:
#         return "SELECT COUNT(*) as total_customers FROM customers;"

#     if "all customers" in prompt_lower and "email" in prompt_lower:
#         return '''
#             SELECT c.name as customer_name, c.email, b.name as branch_name, b.location
#             FROM customers c
#             JOIN branches b ON c.branch_id = b.id;
#         '''

#     if "total amount spent" in prompt_lower and "customer" in prompt_lower:
#         return '''
#             SELECT c.name AS customer_name, SUM(t.amount) AS total_spent
#             FROM customers c
#             JOIN transactions t ON c.id = t.customer_id
#             GROUP BY c.id;
#         '''

#     if "highest transaction" in prompt_lower:
#         return '''
#             SELECT c.name AS customer_name, t.amount, t.date, t.category
#             FROM transactions t
#             JOIN customers c ON t.customer_id = c.id
#             ORDER BY t.amount DESC
#             LIMIT 1;
#         '''

#     if "transactions per category" in prompt_lower or "number of transactions" in prompt_lower:
#         return '''
#             SELECT category, COUNT(*) as count, SUM(amount) as total_amount
#             FROM transactions
#             GROUP BY category;
#         '''

#     try:
#         tokens = word_tokenize(prompt, preserve_line=True)
#         tagged = pos_tag(tokens)
#         named_entities = ne_chunk(tagged)

#         def extract_named_entities(tree):
#             entities = []
#             for subtree in tree:
#                 if isinstance(subtree, Tree):
#                     entity = " ".join([token for token, pos in subtree.leaves()])
#                     entities.append(entity)
#             return entities

#         entities = extract_named_entities(named_entities)

#         for entity in entities:
#             if "Chase" in entity:
#                 return f'''
#                     SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#                     FROM customers c
#                     JOIN branches b ON c.branch_id = b.id
#                     WHERE b.name LIKE '%{entity}%';
#                 '''

#         if "new york" in prompt_lower:
#             return '''
#                 SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#                 FROM customers c
#                 JOIN branches b ON c.branch_id = b.id
#                 WHERE b.location LIKE '%New York%';
#             '''

#     except:
#         pass

#     return "UNSUPPORTED"





## nlp model
# import re
# from nltk.tokenize import word_tokenize
# from nltk import pos_tag, ne_chunk
# from nltk.tree import Tree

# # SQL query templates
# SQL_TEMPLATES = {
#     "total_branches": "SELECT COUNT(*) as total_branches FROM branches;",
#     "all_branches": "SELECT name, location FROM branches;",
#     "total_customers": "SELECT COUNT(*) as total_customers FROM customers;",
#     "all_customers": "SELECT * FROM customers;",
#     "customers_with_emails": """
#         SELECT c.name as customer_name, c.email, b.name as branch_name, b.location
#         FROM customers c
#         JOIN branches b ON c.branch_id = b.id;
#     """,
#     "revenue_by_branch": """
#         SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY p.branch_id;
#     """,
#     "avg_staff": """
#         SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY p.branch_id;
#     """,
#     "top_branch_new_customers": """
#         SELECT b.name AS branch_name, SUM(p.new_customers) AS new_customers
#         FROM performance p
#         JOIN branches b ON p.branch_id = b.id
#         GROUP BY p.branch_id
#         ORDER BY new_customers DESC
#         LIMIT 1;
#     """,
#     "total_spent_by_customer": """
#         SELECT c.name AS customer_name, SUM(t.amount) AS total_spent
#         FROM customers c
#         JOIN transactions t ON c.id = t.customer_id
#         GROUP BY c.id;
#     """,
#     "highest_transaction": """
#         SELECT c.name AS customer_name, t.amount, t.date, t.category
#         FROM transactions t
#         JOIN customers c ON t.customer_id = c.id
#         ORDER BY t.amount DESC
#         LIMIT 1;
#     """,
#     "transactions_by_category": """
#         SELECT category, COUNT(*) as count, SUM(amount) as total_amount
#         FROM transactions
#         GROUP BY category;
#     """,
#     "customers_by_branch_name": """
#         SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#         FROM customers c
#         JOIN branches b ON c.branch_id = b.id
#         WHERE b.name LIKE '%{branch}%';
#     """,
#     "customers_by_location": """
#         SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#         FROM customers c
#         JOIN branches b ON c.branch_id = b.id
#         WHERE b.location LIKE '%{location}%';
#     """
# }


# def extract_named_entities(prompt: str):
#     try:
#         tokens = word_tokenize(prompt)
#         tagged = pos_tag(tokens)
#         chunked = ne_chunk(tagged)

#         entities = []
#         for subtree in chunked:
#             if isinstance(subtree, Tree):
#                 entity = " ".join([token for token, pos in subtree.leaves()])
#                 entities.append(entity)
#         return entities
#     except:
#         return []


# def generate_sql_query(prompt: str) -> str:
#     prompt_lower = prompt.lower()
#     entities = extract_named_entities(prompt)

#     # Keyword-based mapping
#     if re.search(r"\btotal (number of )?branches\b", prompt_lower):
#         return SQL_TEMPLATES["total_branches"]

#     if re.search(r"\b(all|list|show) branches\b", prompt_lower):
#         return SQL_TEMPLATES["all_branches"]

#     if re.search(r"\btotal (number of )?customers\b", prompt_lower) or "how many customers" in prompt_lower:
#         return SQL_TEMPLATES["total_customers"]

#     if "all customers" in prompt_lower and "email" in prompt_lower:
#         return SQL_TEMPLATES["customers_with_emails"]

#     if re.search(r"\b(all|list|show) customers\b", prompt_lower):
#         return SQL_TEMPLATES["all_customers"]

#     if "total revenue" in prompt_lower and "branch" in prompt_lower:
#         return SQL_TEMPLATES["revenue_by_branch"]

#     if "average staff" in prompt_lower or "staff count" in prompt_lower:
#         return SQL_TEMPLATES["avg_staff"]

#     if "highest number of new customers" in prompt_lower or "top branch new customers" in prompt_lower:
#         return SQL_TEMPLATES["top_branch_new_customers"]

#     if "total amount spent" in prompt_lower and "customer" in prompt_lower:
#         return SQL_TEMPLATES["total_spent_by_customer"]

#     if "highest transaction" in prompt_lower:
#         return SQL_TEMPLATES["highest_transaction"]

#     if "transactions per category" in prompt_lower or "transactions by category" in prompt_lower:
#         return SQL_TEMPLATES["transactions_by_category"]

#     # Named Entity Handling for location/branch
#     for entity in entities:
#         if "Chase" in entity or "Bank" in entity or "Branch" in entity:
#             return SQL_TEMPLATES["customers_by_branch_name"].format(branch=entity)
#         if "New York" in entity or "Los Angeles" in entity or "Chicago" in entity:
#             return SQL_TEMPLATES["customers_by_location"].format(location=entity)

#     return "UNSUPPORTED"












# # sql_mapper.py

# from typing import List

# # ✅ Centralized intent-slot to SQL template mapping
# MAPPINGS = [
#     {
#         "intent": "total_customers",
#         "keywords": ["total customers", "how many customers"],
#         "sql": "SELECT COUNT(*) AS total_customers FROM customers;"
#     },
#     {
#         "intent": "all_customers",
#         "keywords": ["all customers", "list all customers", "show all customers"],
#         "sql": "SELECT * FROM customers;"
#     },
#     {
#         "intent": "customers_with_emails",
#         "keywords": ["all customers", "email"],
#         "sql": """
#             SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#             FROM customers c
#             JOIN branches b ON c.branch_id = b.id;
#         """
#     },
#     {
#         "intent": "total_branches",
#         "keywords": ["total number of branches"],
#         "sql": "SELECT COUNT(*) AS total_branches FROM branches;"
#     },
#     {
#         "intent": "branch_locations",
#         "keywords": ["branch locations", "list all branches", "show all branches"],
#         "sql": "SELECT name, location FROM branches;"
#     },
#     {
#         "intent": "revenue_by_branch",
#         "keywords": ["total revenue", "branch"],
#         "sql": """
#             SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id;
#         """
#     },
#     {
#         "intent": "highest_new_customers_branch",
#         "keywords": ["highest number of new customers"],
#         "sql": """
#             SELECT b.name AS branch_name, SUM(p.new_customers) AS new_customers
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id
#             ORDER BY new_customers DESC
#             LIMIT 1;
#         """
#     },
#     {
#         "intent": "average_staff_count",
#         "keywords": ["average staff", "staff count"],
#         "sql": """
#             SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff
#             FROM performance p
#             JOIN branches b ON p.branch_id = b.id
#             GROUP BY p.branch_id;
#         """
#     },
#     {
#         "intent": "total_spent_per_customer",
#         "keywords": ["total amount spent", "customer"],
#         "sql": """
#             SELECT c.name AS customer_name, SUM(t.amount) AS total_spent
#             FROM customers c
#             JOIN transactions t ON c.id = t.customer_id
#             GROUP BY c.id;
#         """
#     },
#     {
#         "intent": "highest_transaction",
#         "keywords": ["highest transaction"],
#         "sql": """
#             SELECT c.name AS customer_name, t.amount, t.date, t.category
#             FROM transactions t
#             JOIN customers c ON t.customer_id = c.id
#             ORDER BY t.amount DESC
#             LIMIT 1;
#         """
#     },
#     {
#         "intent": "transactions_by_category",
#         "keywords": ["transactions per category", "number of transactions", "category"],
#         "sql": """
#             SELECT category, COUNT(*) as count, SUM(amount) as total_amount
#             FROM transactions
#             GROUP BY category;
#         """
#     },
#     {
#         "intent": "customers_in_new_york",
#         "keywords": ["new york"],
#         "sql": """
#             SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location
#             FROM customers c
#             JOIN branches b ON c.branch_id = b.id
#             WHERE b.location LIKE '%New York%';
#         """
#     }
# ]

# # ✅ Helper: Match prompt using keyword combinations
# def match_intent(prompt: str) -> str:
#     prompt_lower = prompt.lower()
#     for item in MAPPINGS:
#         if all(keyword in prompt_lower for keyword in item["keywords"]):
#             return item["sql"]
#     return "UNSUPPORTED"

# # ✅ Main function to generate SQL
# def generate_sql_query(prompt: str) -> str:
#     return match_intent(prompt)


# ## nlp

# import nltk
# from nltk.tokenize import word_tokenize
# from nltk import pos_tag, ne_chunk
# from nltk.tree import Tree

# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')

# # Define SQL templates with slots
# SQL_TEMPLATES = {
#     "total_customers": "SELECT COUNT(*) as total_customers FROM customers;",
#     "all_customers": "SELECT * FROM customers;",
#     "customers_with_emails": "SELECT c.name as customer_name, c.email, b.name as branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id;",
#     "revenue_by_branch": "SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue FROM performance p JOIN branches b ON p.branch_id = b.id GROUP BY p.branch_id;",
#     "avg_staff": "SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff FROM performance p JOIN branches b ON p.branch_id = b.id GROUP BY p.branch_id;",
#     "transactions_per_category": "SELECT category, COUNT(*) as count, SUM(amount) as total_amount FROM transactions GROUP BY category;",
#     "highest_transaction": "SELECT c.name AS customer_name, t.amount, t.date, t.category FROM transactions t JOIN customers c ON t.customer_id = c.id ORDER BY t.amount DESC LIMIT 1;",
#     "total_spent_by_customer": "SELECT c.name AS customer_name, SUM(t.amount) AS total_spent FROM customers c JOIN transactions t ON c.id = t.customer_id GROUP BY c.id;",
#     "branch_customers": "SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id WHERE b.name ILIKE '%{branch_name}%';",
#     "location_customers": "SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id WHERE b.location ILIKE '%{location}%';"
# }

# def extract_named_entities(prompt):
#     tokens = word_tokenize(prompt)
#     tagged = pos_tag(tokens)
#     tree = ne_chunk(tagged, binary=False)

#     entities = []
#     for subtree in tree:
#         if isinstance(subtree, Tree):
#             entity = " ".join([token for token, pos in subtree.leaves()])
#             entities.append(entity)
#     return entities

# def detect_intent(prompt_lower):
#     if "how many" in prompt_lower and "customers" in prompt_lower:
#         return "total_customers"
#     if "list" in prompt_lower or "show all customers" in prompt_lower:
#         return "all_customers"
#     if "email" in prompt_lower and "customers" in prompt_lower:
#         return "customers_with_emails"
#     if "total revenue" in prompt_lower:
#         return "revenue_by_branch"
#     if "average staff" in prompt_lower or "staff count" in prompt_lower:
#         return "avg_staff"
#     if "transactions" in prompt_lower and "category" in prompt_lower:
#         return "transactions_per_category"
#     if "highest transaction" in prompt_lower:
#         return "highest_transaction"
#     if "total amount" in prompt_lower and "customer" in prompt_lower:
#         return "total_spent_by_customer"
#     return None

# def generate_sql_query(prompt: str) -> str:
#     prompt_lower = prompt.lower()
#     intent = detect_intent(prompt_lower)

#     if intent:
#         return SQL_TEMPLATES[intent]

#     # If no intent found, fallback to entity-based query
#     entities = extract_named_entities(prompt)
#     for entity in entities:
#         if "chase" in entity.lower():
#             return SQL_TEMPLATES["branch_customers"].format(branch_name=entity)
#         elif "york" in entity.lower():
#             return SQL_TEMPLATES["location_customers"].format(location=entity)

#     return "UNSUPPORTED"

# # Example usage
# if __name__ == "__main__":
#     queries = [
#         "How many customers do we have?",
#         "List all customers with their emails",
#         "What is the total revenue by branch?",
#         "Average staff count per branch?",
#         "Show all customers from Chase Manhattan NY",
#         "Customers from New York"
#     ]
#     for q in queries:
#         print("Prompt:", q)
#         print("SQL Query:", generate_sql_query(q))
#         print("---")




# import nltk
# from nltk.tokenize import word_tokenize
# from nltk import pos_tag, ne_chunk
# from nltk.tree import Tree

# import nltk
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')

# # Expanded SQL templates with additional logic
# SQL_TEMPLATES = {
#     "total_customers": "SELECT COUNT(*) as total_customers FROM customers;",
#     "all_customers": "SELECT * FROM customers;",
#     "customers_with_emails": "SELECT c.name as customer_name, c.email, b.name as branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id;",
#     "revenue_by_branch": "SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue FROM performance p JOIN branches b ON p.branch_id = b.id GROUP BY p.branch_id;",
#     "avg_staff": "SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff FROM performance p JOIN branches b ON p.branch_id = b.id GROUP BY p.branch_id;",
#     "transactions_per_category": "SELECT category, COUNT(*) as count, SUM(amount) as total_amount FROM transactions GROUP BY category;",
#     "highest_transaction": "SELECT c.name AS customer_name, t.amount, t.date, t.category FROM transactions t JOIN customers c ON t.customer_id = c.id ORDER BY t.amount DESC LIMIT 1;",
#     "total_spent_by_customer": "SELECT c.name AS customer_name, SUM(t.amount) AS total_spent FROM customers c JOIN transactions t ON c.id = t.customer_id GROUP BY c.id;",
#     "branch_customers": "SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id WHERE b.name ILIKE '%{branch_name}%';",
#     "location_customers": "SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location FROM customers c JOIN branches b ON c.branch_id = b.id WHERE b.location ILIKE '%{location}%';",
#     "branch_locations": "SELECT DISTINCT location FROM branches;",
#     "total_branches": "SELECT COUNT(*) AS total_branches FROM branches;",
#     "top_branch_new_customers": "SELECT b.name AS branch_name, SUM(p.number_of_new_customers) AS total_new_customers FROM performance p JOIN branches b ON p.branch_id = b.id GROUP BY b.id ORDER BY total_new_customers DESC LIMIT 1;",
#     "top_customer_spent": "SELECT c.name AS customer_name, SUM(t.amount) AS total_spent FROM customers c JOIN transactions t ON c.id = t.customer_id GROUP BY c.id ORDER BY total_spent DESC LIMIT 1;"
# }

# # Keyword mapping for flexible prompt handling
# INTENT_KEYWORDS = [
#     ("total_customers", ["how many", "total", "customers"]),
#     ("all_customers", ["list all", "show all", "customers"]),
#     ("customers_with_emails", ["email", "customers"]),
#     ("revenue_by_branch", ["total revenue", "revenue", "branch"]),
#     ("avg_staff", ["average staff", "staff count"]),
#     ("transactions_per_category", ["transactions", "category"]),
#     ("highest_transaction", ["highest transaction", "biggest transaction"]),
#     ("total_spent_by_customer", ["total amount", "total spent", "each customer"]),
#     ("branch_locations", ["list branch locations", "branch locations"]),
#     ("total_branches", ["total number of branches", "how many branches"]),
#     ("top_branch_new_customers", ["highest number of new customers", "most new customers"]),
#     ("top_customer_spent", ["customer spent the most", "highest spender"])
# ]

# def extract_named_entities(prompt):
#     tokens = word_tokenize(prompt)
#     tagged = pos_tag(tokens)
#     tree = ne_chunk(tagged, binary=False)

#     entities = []
#     for subtree in tree:
#         if isinstance(subtree, Tree):
#             entity = " ".join([token for token, pos in subtree.leaves()])
#             entities.append(entity)
#     return entities

# def detect_intent(prompt_lower):
#     for intent, keywords in INTENT_KEYWORDS:
#         if all(keyword in prompt_lower for keyword in keywords):
#             return intent
#     return None

# def generate_sql_query(prompt: str) -> str:
#     prompt_lower = prompt.lower()
#     intent = detect_intent(prompt_lower)

#     if intent:
#         return SQL_TEMPLATES[intent]

#     # Try fallback entity-based logic
#     entities = extract_named_entities(prompt)
#     for entity in entities:
#         if "chase" in entity.lower():
#             return SQL_TEMPLATES["branch_customers"].format(branch_name=entity)
#         elif any(loc in entity.lower() for loc in ["york", "austin", "chicago"]):
#             return SQL_TEMPLATES["location_customers"].format(location=entity)

#     return "UNSUPPORTED"

# # Example usage
# if __name__ == "__main__":
#     queries = [
#         "List all branch locations.",
#         "What is the total number of branches?",
#         "Which branch had the highest number of new customers?",
#         "Which customer spent the most?",
#         "List all customers with their branch names and emails",
#         "What is the total revenue by branch?",
#     ]
#     for q in queries:
#         print("Prompt:", q)
#         print("SQL Query:", generate_sql_query(q))
#         print("---")



# from nlp_utils import extract_lemmas

# # SQL Templates
# SQL_TEMPLATES = {
#     "total_customers": "SELECT COUNT(*) as total_customers FROM customers;",
#     "all_customers": "SELECT * FROM customers;",
#     "customers_with_emails": """SELECT c.name as customer_name, c.email, b.name as branch_name, b.location 
#                                 FROM customers c JOIN branches b ON c.branch_id = b.id;""",
#     "revenue_by_branch": """SELECT b.name AS branch_name, SUM(p.revenue) AS total_revenue 
#                             FROM performance p JOIN branches b ON p.branch_id = b.id 
#                             GROUP BY p.branch_id;""",
#     "avg_staff": """SELECT b.name AS branch_name, AVG(p.staff_count) AS avg_staff 
#                     FROM performance p JOIN branches b ON p.branch_id = b.id 
#                     GROUP BY p.branch_id;""",
#     "transactions_per_category": """SELECT category, COUNT(*) as count, SUM(amount) as total_amount 
#                                     FROM transactions GROUP BY category;""",
#     "highest_transaction": """SELECT c.name AS customer_name, t.amount, t.date, t.category 
#                               FROM transactions t JOIN customers c ON t.customer_id = c.id 
#                               ORDER BY t.amount DESC LIMIT 1;""",
#     "total_spent_by_customer": """SELECT c.name AS customer_name, SUM(t.amount) AS total_spent 
#                                   FROM customers c JOIN transactions t ON c.id = t.customer_id 
#                                   GROUP BY c.id;""",
#     "branch_customers": """SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location 
#                            FROM customers c JOIN branches b ON c.branch_id = b.id 
#                            WHERE b.name ILIKE '%{branch_name}%';""",
#     "location_customers": """SELECT c.name AS customer_name, c.email, b.name AS branch_name, b.location 
#                              FROM customers c JOIN branches b ON c.branch_id = b.id 
#                              WHERE b.location ILIKE '%{location}%';""",
#     "branch_locations": "SELECT DISTINCT location FROM branches;",
#     "total_branches": "SELECT COUNT(*) AS total_branches FROM branches;",
#     "top_branch_new_customers": """SELECT b.name AS branch_name, SUM(p.number_of_new_customers) AS total_new_customers 
#                                    FROM performance p JOIN branches b ON p.branch_id = b.id 
#                                    GROUP BY b.id ORDER BY total_new_customers DESC LIMIT 1;""",
#     "top_customer_spent": """SELECT c.name AS customer_name, SUM(t.amount) AS total_spent 
#                              FROM customers c JOIN transactions t ON c.id = t.customer_id 
#                              GROUP BY c.id ORDER BY total_spent DESC LIMIT 1;"""
# }

# # Keywords (lemmatized) per intent
# INTENT_KEYWORDS = {
#     "total_customers": ["total", "customer"],
#     "all_customers": ["list", "customer"],
#     "customers_with_emails": ["email", "customer"],
#     "revenue_by_branch": ["revenue", "branch"],
#     "avg_staff": ["average", "staff"],
#     "transactions_per_category": ["transaction", "category"],
#     "highest_transaction": ["highest", "transaction"],
#     "total_spent_by_customer": ["total", "spend", "customer"],
#     "branch_locations": ["branch", "location"],
#     "total_branches": ["total", "branch"],
#     "top_branch_new_customers": ["most", "new", "customer", "branch"],
#     "top_customer_spent": ["customer", "spend", "most"]
# }

# def detect_intent(prompt: str):
#     lemmas = extract_lemmas(prompt)
#     intent_scores = {}

#     for intent, keywords in INTENT_KEYWORDS.items():
#         match_count = sum(1 for kw in keywords if kw in lemmas)
#         intent_scores[intent] = match_count

#     # Sort by best match
#     best_intent = max(intent_scores, key=intent_scores.get)
#     if intent_scores[best_intent] > 0:
#         return best_intent

#     return None

# def generate_sql_query(prompt: str) -> str:
#     intent = detect_intent(prompt)

#     if intent and intent in SQL_TEMPLATES:
#         return SQL_TEMPLATES[intent]

#     # Fallback basic rule-based entity matching
#     lower = prompt.lower()
#     if "new york" in lower or "austin" in lower or "chicago" in lower:
#         city = "new york" if "new york" in lower else "austin" if "austin" in lower else "chicago"
#         return SQL_TEMPLATES["location_customers"].format(location=city)
#     if "chase" in lower:
#         return SQL_TEMPLATES["branch_customers"].format(branch_name="Chase")

#     return "Sorry, I couldn't understand the question."




import spacy
from nlp_utils import extract_noun_chunks, extract_lemmas, extract_named_entities

nlp = spacy.load("en_core_web_sm")

# ----------------------
# Core SQL Builder
# ----------------------
def build_sql(table, select_fields, where_clause=None, joins=None, group_by=None, order_by=None, limit=None):
    sql = f"SELECT {', '.join(select_fields)} FROM {table}"
    if joins:
        for join in joins:
            sql += f" JOIN {join['table']} ON {join['on']}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if group_by:
        sql += f" GROUP BY {group_by}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit:
        sql += f" LIMIT {limit}"
    return sql

# ----------------------
# Main Query Generator
# ----------------------
def generate_sql_query(prompt: str) -> str:
    doc = nlp(prompt)
    noun_chunks = extract_noun_chunks(doc)
    lemmas = extract_lemmas(doc)
    entities = extract_named_entities(doc)

    prompt_lower = prompt.lower()

    # --- Dynamic SQL Logic Based on Lemmas & Noun Phrases ---

    if "location" in lemmas and "branch" in lemmas:
        return build_sql(table="branches", select_fields=["location"])

    if "total" in lemmas and "branch" in lemmas:
        return build_sql(table="branches", select_fields=["COUNT(*) AS total_branches"])

    if "revenue" in lemmas and "branch" in lemmas:
        return build_sql(
            table="performance p",
            select_fields=["b.name AS branch_name", "SUM(p.revenue) AS total_revenue"],
            joins=[{"table": "branches b", "on": "p.branch_id = b.id"}],
            group_by="p.branch_id"
        )

    if "staff" in lemmas and ("average" in lemmas or "avg" in lemmas):
        return build_sql(
            table="performance p",
            select_fields=["b.name AS branch_name", "AVG(p.staff_count) AS avg_staff"],
            joins=[{"table": "branches b", "on": "p.branch_id = b.id"}],
            group_by="p.branch_id"
        )

    if "email" in lemmas and "customer" in lemmas:
        return build_sql(
            table="customers c",
            select_fields=["c.name AS customer_name", "c.email", "b.name AS branch_name", "b.location"],
            joins=[{"table": "branches b", "on": "c.branch_id = b.id"}]
        )

    if "transaction" in lemmas and "category" in lemmas:
        return build_sql(
            table="transactions",
            select_fields=["category", "COUNT(*) AS count", "SUM(amount) AS total_amount"],
            group_by="category"
        )

    if "spent" in lemmas and "customer" in lemmas:
        return build_sql(
            table="customers c",
            select_fields=["c.name AS customer_name", "SUM(t.amount) AS total_spent"],
            joins=[{"table": "transactions t", "on": "c.id = t.customer_id"}],
            group_by="c.id"
        )

    if "highest" in lemmas and "transaction" in lemmas:
        return build_sql(
            table="transactions t",
            select_fields=["c.name AS customer_name", "t.amount", "t.date", "t.category"],
            joins=[{"table": "customers c", "on": "t.customer_id = c.id"}],
            order_by="t.amount DESC",
            limit=1
        )

    if "all" in lemmas and "customer" in lemmas:
        return build_sql(
            table="customers",
            select_fields=["*"]
        )

    return "UNSUPPORTED QUERY"

# Optional for import clarity
__all__ = ["generate_sql_query"]
