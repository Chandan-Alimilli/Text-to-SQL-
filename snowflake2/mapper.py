# import re
# import json
# import spacy
# import os
# from datetime import datetime
# from dateutil import parser
# import logging

# from mapper_utils import (
#     extract_entities,
#     extract_direct_column_filters,
#     extract_comparative_filters,
#     parse_date_range_from_prompt,
#     normalize_text
# )
# from prompt_utils import extract_limit_from_prompt
# from rag_retriever import schema_metadata
# from aggregation_handler import detect_aggregation, build_aggregation_query, is_percentage_prompt
# from followup_handler import is_follow_up_prompt

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# nlp = spacy.load("en_core_web_sm")

# # Load business_mapping.json
# business_terms_path = "data/business_mapping.json"
# business_terms = {}
# if os.path.exists(business_terms_path):
#     try:
#         with open(business_terms_path, "r") as f:
#             business_content = f.read().strip()
#             if business_content:
#                 business_terms = json.loads(business_content)
#                 logger.debug("Successfully loaded business_mapping.json")
#                 logger.debug(f"Business terms keys: {list(business_terms.keys())}")
#             else:
#                 logger.error("business_mapping.json is empty")
#     except Exception as e:
#         logger.error(f"Error loading business_mapping.json: {str(e)}")
# else:
#     logger.error(f"Business mapping file not found: {business_terms_path}")

# def generate_sql_query(prompt, matched_table=None, matched_metadata=None, rag_data=None, schema_metadata=schema_metadata, from_date=None, to_date=None, limit=None, memory_context=None):
#     """Generate SQL query from prompt, prioritizing business term mappings."""
#     prompt_lower = prompt.lower()
#     logger.debug(f"Generating SQL for prompt: {prompt_lower}")
#     logger.debug(f"Prompt lower: {prompt_lower}")

#     # Initialize variables
#     table_name = None
#     where_clauses = []
#     applied_business_terms = []

#     # Apply business rules for table selection and conditions
#     for key, rule in business_terms.items():
#         logger.debug(f"Checking business term: {key}")
#         if key in prompt_lower and (not table_name or rule["table"].upper() == table_name):
#             col = rule["column"].upper()
#             if rule.get("not_null"):
#                 where_clauses.append(f"{col} IS NOT NULL")
#                 logger.debug(f"Applied business rule: {col} IS NOT NULL for key {key}")
#             elif rule.get("is_null"):
#                 where_clauses.append(f"{col} IS NULL")
#                 logger.debug(f"Applied business rule: {col} IS NULL for key {key}")
#             elif "value" in rule:
#                 val = rule["value"]
#                 val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
#                 where_clauses.append(f"{col} = {val}")
#                 logger.debug(f"Applied business rule: {col} = {val} for key {key}")
#             applied_business_terms.append(key)
#             if not table_name:
#                 table_name = rule["table"].upper()
#                 logger.debug(f"Selected table {table_name} via business term: {key}")

#     # Determine table and metadata if not set by business terms
#     if not table_name and matched_table:
#         if isinstance(matched_table, str):
#             table_name = matched_table.upper()
#             metadata = schema_metadata.get(table_name, {})
#             if not metadata:
#                 # Try case-insensitive lookup
#                 for key in schema_metadata:
#                     if key.upper() == table_name:
#                         metadata = schema_metadata[key]
#                         table_name = key.upper()
#                         logger.debug(f"Case-insensitive match for table: {table_name}")
#                         break
#         elif isinstance(matched_table, dict):
#             table_name = list(matched_table.keys())[0].upper()
#             metadata = matched_table[table_name]
#         else:
#             logger.error("Invalid matched_table structure")
#             raise Exception("Invalid matched_table structure.")
#     elif not table_name:
#         logger.error("Could not determine table for prompt")
#         raise Exception("❌ Could not determine table for prompt")

#     # Fallback to rag_data if metadata is missing
#     metadata = schema_metadata.get(table_name, {})
#     if not metadata and rag_data:
#         for rag_table, rag_meta in rag_data.items():
#             if rag_table.upper() == table_name:
#                 metadata = rag_meta
#                 logger.debug(f"Using rag_data metadata for table: {table_name}")
#                 break

#     if not metadata:
#         logger.error(f"No metadata found for table: {table_name}")
#         raise Exception(f"No metadata found for table: {table_name}")

#     table_name_upper = table_name.upper()
#     columns_meta = metadata.get("columns", {})
#     fields = extract_entities(prompt)

#     if not applied_business_terms and not is_follow_up_prompt(prompt):
#         logger.warning(f"No business terms matched for prompt: {prompt}")

#     # Detect aggregation
#     force_count = any(kw in prompt_lower for kw in ["how many", "number of"])
#     if force_count:
#         agg_func = "COUNT"
#         agg_col = None
#     else:
#         try:
#             agg_func, agg_col = detect_aggregation(prompt, dict(columns_meta))
#         except Exception:
#             agg_func, agg_col = None, None
#         logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

#     # Fallback column for COUNT
#     if agg_func == "COUNT" and not agg_col:
#         numeric_col = next(
#             (col for col, meta in columns_meta.items()
#              if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
#             None
#         )
#         agg_col = numeric_col or "*"
#         logger.debug(f"Selected COUNT column: {agg_col}")

#     # Handle percentage logic
#     if agg_func == "PERCENTAGE":
#         if not agg_col:
#             for key, rule in business_terms.items():
#                 if key in prompt_lower and rule["table"].upper() == table_name_upper:
#                     agg_col = rule["column"].upper()
#                     break
#         if not agg_col:
#             for col, meta in columns_meta.items():
#                 if isinstance(meta, dict) and meta.get("type") == "boolean":
#                     agg_col = col
#                     break
#         if not agg_col:
#             logger.error("Could not infer condition column for percentage query")
#             raise Exception("❌ Could not infer condition column for percentage query")

#     # Build aggregation query if needed
#     if agg_func:
#         try:
#             query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, dict(columns_meta))
#             if where_clauses:
#                 where_clause = " WHERE " + " AND ".join(where_clauses)
#                 query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE)
#                 if "LIMIT" not in query.upper():
#                     limit = extract_limit_from_prompt(prompt) or 50
#                     query += f" LIMIT {limit}"
#             logger.info(f"Generated aggregation SQL: {query}")
#             return query
#         except Exception as e:
#             logger.error(f"Aggregation query failed: {str(e)}")
#             raise Exception(f"❌ Aggregation query failed: {str(e)}")

#     # Date range logic
#     inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
#     from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
#     to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to

#     date_cols = [col for col, meta in columns_meta.items()
#                  if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
#     if (from_dt or to_dt) and date_cols:
#         date_col = date_cols[0].upper()
#         if from_dt:
#             where_clauses.append(f"{date_col} >= '{from_dt}'")
#         if to_dt:
#             where_clauses.append(f"{date_col} <= '{to_dt}'")
#         logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

#     # Other filters
#     try:
#         where_clauses += extract_comparative_filters(prompt, dict(columns_meta))
#         where_clauses += extract_direct_column_filters(prompt, dict(columns_meta))
#         logger.debug(f"Additional filters applied: {where_clauses}")
#     except Exception as e:
#         logger.error(f"Filter extraction failed: {str(e)}")
#         raise Exception(f"❌ Filter extraction failed: {str(e)}")

#     # Columns to SELECT
#     selected_cols = [col.upper() for col in columns_meta.keys()]
#     query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
#     if where_clauses:
#         query += " WHERE " + " AND ".join(where_clauses)
#     else:
#         logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
#     query += f" LIMIT {limit or extract_limit_from_prompt(prompt) or 50}"
#     logger.info(f"Generated SQL: {query}")
#     return query










































# import re
# import json
# import spacy
# import os
# from datetime import datetime
# from dateutil import parser
# import logging

# from mapper_utils import (
#     extract_entities,
#     extract_direct_column_filters,
#     extract_comparative_filters,
#     parse_date_range_from_prompt,
#     normalize_text
# )
# from prompt_utils import extract_limit_from_prompt
# from rag_retriever import schema_metadata
# from aggregation_handler import detect_aggregation, build_aggregation_query, is_percentage_prompt
# from followup_handler import is_follow_up_prompt

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# nlp = spacy.load("en_core_web_sm")

# # Load business_mapping.json
# business_terms_path = "data/business_mapping.json"
# business_terms = {}
# if os.path.exists(business_terms_path):
#     try:
#         with open(business_terms_path, "r") as f:
#             business_content = f.read().strip()
#             if business_content:
#                 business_terms = json.loads(business_content)
#                 logger.debug("Successfully loaded business_mapping.json")
#                 logger.debug(f"Business terms keys: {list(business_terms.keys())}")
#             else:
#                 logger.error("business_mapping.json is empty")
#     except Exception as e:
#         logger.error(f"Error loading business_mapping.json: {str(e)}")
# else:
#     logger.error(f"Business mapping file not found: {business_terms_path}")

# def generate_sql_query(prompt, matched_table=None, matched_metadata=None, rag_data=None, schema_metadata=schema_metadata, from_date=None, to_date=None, limit=None, memory_context=None):
#     """Generate SQL query from prompt, prioritizing business term mappings."""
#     prompt_lower = prompt.lower()
#     logger.debug(f"Generating SQL for prompt: {prompt_lower}")

#     # Initialize variables
#     table_name = None
#     where_clauses = []
#     applied_business_terms = []

#     # Apply business rules for table selection and conditions
#     for key, rule in business_terms.items():
#         logger.debug(f"Checking business term: {key}")
#         if key in prompt_lower and (not table_name or rule["table"].upper() == table_name):
#             col = rule["column"].upper()
#             if rule.get("not_null"):
#                 where_clauses.append(f"{col} IS NOT NULL")
#                 logger.debug(f"Applied business rule: {col} IS NOT NULL for key {key}")
#             elif rule.get("is_null"):
#                 where_clauses.append(f"{col} IS NULL")
#                 logger.debug(f"Applied business rule: {col} IS NULL for key {key}")
#             elif "value" in rule:
#                 val = rule["value"]
#                 val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
#                 where_clauses.append(f"{col} = {val}")
#                 logger.debug(f"Applied business rule: {col} = {val} for key {key}")
#             applied_business_terms.append(key)
#             if not table_name:
#                 table_name = rule["table"].upper()
#                 logger.debug(f"Selected table {table_name} via business term: {key}")

#     # Determine table and metadata if not set by business terms
#     if not table_name and matched_table:
#         if isinstance(matched_table, str):
#             table_name = matched_table.upper()
#             metadata = schema_metadata.get(table_name, {})
#             if not metadata:
#                 # Case-insensitive lookup
#                 for key in schema_metadata:
#                     if key.upper() == table_name:
#                         metadata = schema_metadata[key]
#                         table_name = key.upper()
#                         logger.debug(f"Case-insensitive match for table: {table_name}")
#                         break
#                 if not metadata and rag_data:
#                     for rag_table in rag_data:
#                         if rag_table.upper() == table_name:
#                             metadata = rag_data[rag_table]
#                             table_name = rag_table.upper()
#                             logger.debug(f"Fallback to rag_data for table: {table_name}")
#                             break
#         elif isinstance(matched_table, dict):
#             table_name = list(matched_table.keys())[0].upper()
#             metadata = matched_table[table_name]
#         else:
#             logger.error("Invalid matched_table structure")
#             raise Exception("Invalid matched_table structure.")
#     elif not table_name and memory_context:
#         for mem in reversed(memory_context[-3:]):
#             last_sql = mem.get("sql", "")
#             table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
#             if table_match:
#                 table_name = table_match.group(1).upper()
#                 metadata = schema_metadata.get(table_name, {})
#                 if metadata:
#                     logger.debug(f"Inferred table {table_name} from memory context")
#                     break
#     if not table_name:
#         logger.error("Could not determine table for prompt")
#         raise Exception("❌ Could not determine table for prompt")

#     # Ensure metadata is valid
#     metadata = schema_metadata.get(table_name, {})
#     if not metadata and rag_data:
#         for rag_table, rag_meta in rag_data.items():
#             if rag_table.upper() == table_name:
#                 metadata = rag_meta
#                 logger.debug(f"Using rag_data metadata for table: {table_name}")
#                 break
#     if not metadata:
#         logger.error(f"No metadata found for table: {table_name}")
#         raise Exception(f"No metadata found for table: {table_name}")

#     table_name_upper = table_name.upper()
#     columns_meta = metadata.get("columns", {})
#     fields = extract_entities(prompt)

#     if not applied_business_terms and not is_follow_up_prompt(prompt):
#         logger.warning(f"No business terms matched for prompt: {prompt}")

#     # Detect aggregation
#     force_count = any(kw in prompt_lower for kw in ["how many", "number of", "count of"])
#     force_sum = any(kw in prompt_lower for kw in ["sum of", "total"])
#     if force_count:
#         agg_func = "COUNT"
#         agg_col = None
#     elif force_sum:
#         agg_func = "SUM"
#         agg_col = None
#     else:
#         try:
#             agg_func, agg_col = detect_aggregation(prompt, columns_meta)
#         except Exception:
#             agg_func, agg_col = None, None
#         logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

#     # Fallback column for COUNT and SUM
#     if agg_func in ["COUNT", "SUM"]:
#         if not agg_col:
#             # Prefer primary key or unique identifier for COUNT
#             if agg_func == "COUNT":
#                 agg_col = next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("is_primary_key", False)),
#                     None
#                 ) or next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
#                     None
#                 ) or "APPL_NB"  # Default to APPL_NB as common identifier
#                 logger.debug(f"Selected COUNT column: {agg_col}")
#             # For SUM, prefer numeric column mentioned in prompt or metadata
#             elif agg_func == "SUM":
#                 for col, meta in columns_meta.items():
#                     if isinstance(meta, dict) and meta.get("type") == "numeric":
#                         if col.lower() in prompt_lower or meta.get("desc", "").lower() in prompt_lower:
#                             agg_col = col
#                             break
#                 agg_col = agg_col or next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("type") == "numeric"),
#                     None
#                 )
#                 logger.debug(f"Selected SUM column: {agg_col}")

#     # Handle percentage logic
#     if agg_func == "PERCENTAGE":
#         if not agg_col:
#             # Look for business term column
#             for key, rule in business_terms.items():
#                 if key in prompt_lower and rule["table"].upper() == table_name_upper:
#                     agg_col = rule["column"].upper()
#                     where_clauses.append(f"{agg_col} = '{rule['value']}'")
#                     logger.debug(f"Selected PERCENTAGE column from business term: {agg_col}")
#                     break
#             # Fallback to boolean column in prompt
#             if not agg_col:
#                 for col, meta in columns_meta.items():
#                     if isinstance(meta, dict) and meta.get("type") == "boolean":
#                         if col.lower() in prompt_lower or meta.get("desc", "").lower() in prompt_lower:
#                             agg_col = col
#                             where_clauses.append(f"{agg_col} = '1'")
#                             break
#             # Fallback to first boolean column
#             if not agg_col:
#                 agg_col = next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("type") == "boolean"),
#                     None
#                 )
#                 if agg_col:
#                     where_clauses.append(f"{agg_col} = '1'")
#             if not agg_col:
#                 logger.error("Could not infer condition column for percentage query")
#                 raise Exception("❌ Could not infer condition column for percentage query")

#     # Date range logic (applied for all queries)
#     inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
#     from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
#     to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to
#     date_cols = [col for col, meta in columns_meta.items()
#                  if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
#     date_col = date_cols[0].upper() if date_cols else None
#     if (from_dt or to_dt) and date_col:
#         if from_dt and to_dt:
#             where_clauses.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
#         else:
#             if from_dt:
#                 where_clauses.append(f"{date_col} >= '{from_dt}'")
#             if to_dt:
#                 where_clauses.append(f"{date_col} <= '{to_dt}'")
#         logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

#     # Extract filters, prioritizing comparative over direct
#     try:
#         comparative_filters = extract_comparative_filters(prompt, columns_meta)
#         direct_filters = extract_direct_column_filters(prompt, columns_meta) if not comparative_filters else []
#         additional_filters = comparative_filters + direct_filters
#         additional_filters = list(dict.fromkeys(additional_filters))  # Remove duplicates
#         where_clauses += additional_filters
#         logger.debug(f"Applied filters: {where_clauses}")
#     except Exception as e:
#         logger.error(f"Filter extraction failed: {str(e)}")
#         raise Exception(f"❌ Filter extraction failed: {str(e)}")

#     # Build aggregation query if needed
#     if agg_func:
#         try:
#             query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, columns_meta)
#             if where_clauses:
#                 where_clause = " WHERE " + " AND ".join(where_clauses)
#                 query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE) or query + where_clause
#             if "LIMIT" not in query.upper():
#                 limit = extract_limit_from_prompt(prompt) or 50
#                 query += f" LIMIT {limit}"
#             logger.info(f"Generated aggregation SQL: {query}")
#             return query
#         except Exception as e:
#             logger.error(f"Aggregation query failed: {str(e)}")
#             raise Exception(f"❌ Aggregation query failed: {str(e)}")

#     # Default SELECT query
#     selected_cols = [col.upper() for col in columns_meta.keys()]
#     query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
#     if where_clauses:
#         query += " WHERE " + " AND ".join(where_clauses)
#     else:
#         logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
#     query += f" LIMIT {limit or extract_limit_from_prompt(prompt) or 50}"
#     logger.info(f"Generated SQL: {query}")
#     return query



































# import re
# import json
# import spacy
# import os
# from datetime import datetime
# from dateutil import parser
# import logging

# from mapper_utils import (
#     extract_entities,
#     extract_direct_column_filters,
#     extract_comparative_filters,
#     parse_date_range_from_prompt,
#     normalize_text
# )
# from prompt_utils import extract_limit_from_prompt
# from rag_retriever import schema_metadata
# from aggregation_handler import detect_aggregation, build_aggregation_query

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# nlp = spacy.load("en_core_web_sm")

# # Load business_mapping.json
# business_terms_path = "data/business_mapping.json"
# business_terms = {}
# if os.path.exists(business_terms_path):
#     try:
#         with open(business_terms_path, "r") as f:
#             business_content = f.read().strip()
#             if business_content:
#                 business_terms = json.loads(business_content)
#                 logger.debug("Successfully loaded business_mapping.json")
#                 logger.debug(f"Business terms keys: {list(business_terms.keys())}")
#             else:
#                 logger.error("business_mapping.json is empty")
#     except Exception as e:
#         logger.error(f"Error loading business_mapping.json: {str(e)}")
# else:
#     logger.error(f"Business mapping file not found: {business_terms_path}")

# def generate_sql_query(prompt, matched_table=None, matched_metadata=None, rag_data=None, schema_metadata=schema_metadata, from_date=None, to_date=None, limit=None, memory_context=None):
#     """Generate SQL query from prompt, prioritizing business term mappings."""
#     prompt_lower = prompt.lower()
#     logger.debug(f"Generating SQL for prompt: {prompt_lower}")

#     # Initialize variables
#     table_name = None
#     where_clauses = []
#     applied_business_terms = []
#     percentage_condition = None

#     # Handle negated business terms (e.g., "non eligible" or "not eligible")
#     for key, rule in business_terms.items():
#         logger.debug(f"Checking business term: {key}")
#         negated = False
#         term_match = key
#         if "non " + key in prompt_lower or "not " + key in prompt_lower:
#             negated = True
#             term_match = "non " + key if "non " + key in prompt_lower else "not " + key
#         if term_match in prompt_lower and (not table_name or rule["table"].upper() == table_name):
#             col = rule["column"].upper()
#             if rule.get("not_null"):
#                 where_clauses.append(f"{col} IS NOT NULL")
#                 logger.debug(f"Applied business rule: {col} IS NOT NULL for key {key}")
#             elif rule.get("is_null"):
#                 where_clauses.append(f"{col} IS NULL")
#                 logger.debug(f"Applied business rule: {col} IS NULL for key {key}")
#             elif "value" in rule:
#                 val = rule["value"]
#                 val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
#                 if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
#                     if val == "'1'":
#                         val = "'0'"
#                     elif val == "'0'":
#                         val = "'1'"
#                     else:
#                         stripped_val = val.strip("'")
#                         val = f"'Not {stripped_val}'"
#                 where_clauses.append(f"{col} = {val}")
#                 logger.debug(f"Applied business rule: {col} = {val} for key {term_match}")
#                 if "percentage" in prompt_lower or "percent" in prompt_lower:
#                     percentage_condition = f"{col} = {val}"
#             applied_business_terms.append(term_match)
#             if not table_name:
#                 table_name = rule["table"].upper()
#                 logger.debug(f"Selected table {table_name} via business term: {key}")

#     # Determine table and metadata if not set by business terms
#     if not table_name and matched_table:
#         if isinstance(matched_table, str):
#             table_name = matched_table.upper()
#             metadata = schema_metadata.get(table_name, {})
#             if not metadata:
#                 # Case-insensitive lookup
#                 for key in schema_metadata:
#                     if key.upper() == table_name:
#                         metadata = schema_metadata[key]
#                         table_name = key.upper()
#                         logger.debug(f"Case-insensitive match for table: {table_name}")
#                         break
#                 if not metadata and rag_data:
#                     for rag_table in rag_data:
#                         if rag_table.upper() == table_name:
#                             metadata = rag_data[rag_table]
#                             table_name = rag_table.upper()
#                             logger.debug(f"Fallback to rag_data for table: {table_name}")
#                             break
#         elif isinstance(matched_table, dict):
#             table_name = list(matched_table.keys())[0].upper()
#             metadata = matched_table[table_name]
#         else:
#             logger.error("Invalid matched_table structure")
#             raise Exception("Invalid matched_table structure.")
#     elif not table_name and memory_context:
#         for mem in reversed(memory_context[-3:]):
#             last_sql = mem.get("sql", "")
#             table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
#             if table_match:
#                 table_name = table_match.group(1).upper()
#                 metadata = schema_metadata.get(table_name, {})
#                 if metadata:
#                     logger.debug(f"Inferred table {table_name} from memory context")
#                     break
#     if not table_name:
#         logger.error("Could not determine table for prompt")
#         raise Exception("❌ Could not determine table for prompt")

#     # Ensure metadata is valid
#     metadata = schema_metadata.get(table_name, {})
#     if not metadata and rag_data:
#         for rag_table, rag_meta in rag_data.items():
#             if rag_table.upper() == table_name:
#                 metadata = rag_meta
#                 logger.debug(f"Using rag_data metadata for table: {table_name}")
#                 break
#     if not metadata:
#         logger.error(f"No metadata found for table: {table_name}")
#         raise Exception(f"No metadata found for table: {table_name}")

#     table_name_upper = table_name.upper()
#     columns_meta = metadata.get("columns", {})
#     fields = extract_entities(prompt)

#     if not applied_business_terms:
#         logger.warning(f"No business terms matched for prompt: {prompt}")

#     # Detect aggregation
#     force_count = any(kw in prompt_lower for kw in ["how many", "number of", "count of"])
#     force_sum = any(kw in prompt_lower for kw in ["sum of", "total"])
#     if force_count:
#         agg_func = "COUNT"
#         agg_col = None
#     elif force_sum:
#         agg_func = "SUM"
#         agg_col = None
#     else:
#         try:
#             agg_func, agg_col = detect_aggregation(prompt, columns_meta)
#         except Exception:
#             agg_func, agg_col = None, None
#         logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

#     # Fallback column for COUNT and SUM
#     if agg_func in ["COUNT", "SUM"]:
#         if not agg_col:
#             if agg_func == "COUNT":
#                 agg_col = next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
#                     "APPL_NB"  # Default to APPL_NB as common identifier
#                 )
#                 logger.debug(f"Selected COUNT column: {agg_col}")
#             elif agg_func == "SUM":
#                 for col, meta in columns_meta.items():
#                     if isinstance(meta, dict) and meta.get("type") == "numeric":
#                         if col.lower() in prompt_lower or meta.get("desc", "").lower() in prompt_lower:
#                             agg_col = col
#                             break
#                 agg_col = agg_col or next(
#                     (col for col, meta in columns_meta.items()
#                      if isinstance(meta, dict) and meta.get("type") == "numeric"),
#                     None
#                 )
#                 logger.debug(f"Selected SUM column: {agg_col}")

#     # Handle percentage logic
#     if agg_func == "PERCENTAGE":
#         if not percentage_condition:
#             for key, rule in business_terms.items():
#                 negated = "non " + key in prompt_lower or "not " + key in prompt_lower
#                 term_match = "non " + key if "non " + key in prompt_lower else "not " + key if "not " + key in prompt_lower else key
#                 if term_match in prompt_lower and rule["table"].upper() == table_name_upper:
#                     agg_col = rule["column"].upper()
#                     val = rule["value"]
#                     val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
#                     if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
#                         if val == "'1'":
#                             val = "'0'"
#                         elif val == "'0'":
#                             val = "'1'"
#                         else:
#                             stripped_val = val.strip("'")
#                             val = f"'Not {stripped_val}'"
#                     percentage_condition = f"{agg_col} = {val}"
#                     logger.debug(f"Selected PERCENTAGE condition from business term: {percentage_condition}")
#                     break
#         if not percentage_condition:
#             logger.error("Could not infer condition for percentage query")
#             raise Exception("❌ Could not infer condition for percentage query")

#     # Date range logic (applied for all queries)
#     inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
#     from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
#     to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to
#     date_cols = [col for col, meta in columns_meta.items()
#                  if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
#     date_col = date_cols[0].upper() if date_cols else None
#     if (from_dt or to_dt) and date_col:
#         if from_dt and to_dt:
#             where_clauses.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
#         else:
#             if from_dt:
#                 where_clauses.append(f"{date_col} >= '{from_dt}'")
#             if to_dt:
#                 where_clauses.append(f"{date_col} <= '{to_dt}'")
#         logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

#     # Extract filters, prioritizing comparative over direct
#     try:
#         comparative_filters = extract_comparative_filters(prompt, columns_meta)
#         direct_filters = extract_direct_column_filters(prompt, columns_meta)
#         additional_filters = comparative_filters + direct_filters
#         additional_filters = list(dict.fromkeys(additional_filters))  # Remove duplicates
#         where_clauses += additional_filters
#         logger.debug(f"Applied filters: {where_clauses}")
#     except Exception as e:
#         logger.error(f"Filter extraction failed: {str(e)}")
#         raise Exception(f"❌ Filter extraction failed: {str(e)}")

#     # Build aggregation query if needed
#     if agg_func:
#         try:
#             query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, columns_meta, percentage_condition)
#             if where_clauses:
#                 where_clause = " WHERE " + " AND ".join(where_clauses)
#                 query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE) or query + where_clause
#             if "LIMIT" not in query.upper():
#                 limit = extract_limit_from_prompt(prompt) or 50
#                 query += f" LIMIT {limit}"
#             logger.info(f"Generated aggregation SQL: {query}")
#             return query
#         except Exception as e:
#             logger.error(f"Aggregation query failed: {str(e)}")
#             raise Exception(f"❌ Aggregation query failed: {str(e)}")

#     # Default SELECT query
#     selected_cols = [col.upper() for col in columns_meta.keys()]
#     query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
#     if where_clauses:
#         query += " WHERE " + " AND ".join(where_clauses)
#     else:
#         logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
#     query += f" LIMIT {limit or extract_limit_from_prompt(prompt) or 50}"
#     logger.info(f"Generated SQL: {query}")
#     return query
































import re
import json
import spacy
import os
from datetime import datetime
from dateutil import parser
import logging

from mapper_utils import (
    extract_entities,
    extract_direct_column_filters,
    extract_comparative_filters,
    parse_date_range_from_prompt,
    normalize_text
)
from prompt_utils import extract_limit_from_prompt
from rag_retriever import schema_metadata
from aggregation_handler import detect_aggregation, build_aggregation_query

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

nlp = spacy.load("en_core_web_sm")

# Load business_mapping.json
business_terms_path = "data/business_mapping.json"
business_terms = {}
if os.path.exists(business_terms_path):
    try:
        with open(business_terms_path, "r") as f:
            business_content = f.read().strip()
            if business_content:
                business_terms = json.loads(business_content)
                logger.debug("Successfully loaded business_mapping.json")
                logger.debug(f"Business terms keys: {list(business_terms.keys())}")
            else:
                logger.error("business_mapping.json is empty")
    except Exception as e:
        logger.error(f"Error loading business_mapping.json: {str(e)}")
else:
    logger.error(f"Business mapping file not found: {business_terms_path}")

def generate_sql_query(prompt, matched_table=None, matched_metadata=None, rag_data=None, schema_metadata=schema_metadata, from_date=None, to_date=None, limit=None, memory_context=None):
    """Generate SQL query from prompt, prioritizing business term mappings."""
    prompt_lower = prompt.lower()
    logger.debug(f"Generating SQL for prompt: {prompt_lower}")

    # Initialize variables
    table_name = None
    where_clauses = []
    applied_business_terms = []
    percentage_condition = None
    percentage_denominator_condition = None  # For queries like "approved over booked"

    # Handle negated and regular business terms
    for key, rule in business_terms.items():
        logger.debug(f"Checking business term: {key}")
        negated = False
        term_match = key
        if "non " + key in prompt_lower or "not " + key in prompt_lower:
            negated = True
            term_match = "non " + key if "non " + key in prompt_lower else "not " + key
        if term_match in prompt_lower and (not table_name or rule["table"].upper() == table_name):
            col = rule["column"].upper()
            table_name = rule["table"].upper()
            if rule.get("not_null"):
                where_clauses.append(f"{col} IS NOT NULL")
                logger.debug(f"Applied business rule: {col} IS NOT NULL for key {key}")
            elif rule.get("is_null"):
                where_clauses.append(f"{col} IS NULL")
                logger.debug(f"Applied business rule: {col} IS NULL for key {key}")
            elif "value" in rule:
                val = rule["value"]
                val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
                    if val == "'1'":
                        val = "'0'"
                    elif val == "'0'":
                        val = "'1'"
                    else:
                        stripped_val = val.strip("'")
                        val = f"'Not {stripped_val}'"
                condition = f"{col} = {val}"
                where_clauses.append(condition)
                logger.debug(f"Applied business rule: {condition} for key {term_match}")
            applied_business_terms.append(term_match)
            if not table_name:
                table_name = rule["table"].upper()
                logger.debug(f"Selected table {table_name} via business term: {key}")

    # Detect percentage over another business term (e.g., approved over booked)
    percentage_over_match = re.search(r"percentage of (\w+) (?:applications )?over (\w+) applications", prompt_lower)
    if percentage_over_match:
        numerator_term, denominator_term = percentage_over_match.groups()
        numerator_rule = business_terms.get(numerator_term)
        denominator_rule = business_terms.get(denominator_term)
        if numerator_rule and denominator_rule:
            numerator_col = numerator_rule["column"].upper()
            numerator_val = str(numerator_rule["value"]).upper() if isinstance(numerator_rule["value"], bool) or numerator_rule["value"] in ["0", "1"] else f"'{numerator_rule['value']}'"
            denominator_col = denominator_rule["column"].upper()
            denominator_val = str(denominator_rule["value"]).upper() if isinstance(denominator_rule["value"], bool) or denominator_rule["value"] in ["0", "1"] else f"'{denominator_rule['value']}'"
            percentage_condition = f"{numerator_col} = {numerator_val}"
            percentage_denominator_condition = f"{denominator_col} = {denominator_val}"
            table_name = numerator_rule["table"].upper()
            if numerator_rule["table"].upper() != denominator_rule["table"].upper():
                # Cross-table query
                table_name = f"{numerator_rule['table'].upper()} t1 JOIN {denominator_rule['table'].upper()} t2 ON t1.APPL_NB = t2.APPL_NB"
                percentage_condition = f"t1.{numerator_col} = {numerator_val}"
                percentage_denominator_condition = f"t2.{denominator_col} = {denominator_val}"
            logger.debug(f"Percentage over business terms: {percentage_condition} / {percentage_denominator_condition}")

    # Determine table and metadata if not set by business terms
    if not table_name and matched_table:
        if isinstance(matched_table, str):
            table_name = matched_table.upper()
            metadata = schema_metadata.get(table_name, {})
            if not metadata:
                for key in schema_metadata:
                    if key.upper() == table_name:
                        metadata = schema_metadata[key]
                        table_name = key.upper()
                        logger.debug(f"Case-insensitive match for table: {table_name}")
                        break
                if not metadata and rag_data:
                    for rag_table in rag_data:
                        if rag_table.upper() == table_name:
                            metadata = rag_data[rag_table]
                            table_name = rag_table.upper()
                            logger.debug(f"Fallback to rag_data for table: {table_name}")
                            break
        elif isinstance(matched_table, dict):
            table_name = list(matched_table.keys())[0].upper()
            metadata = matched_table[table_name]
        else:
            logger.error("Invalid matched_table structure")
            raise Exception("Invalid matched_table structure.")
    elif not table_name and memory_context:
        for mem in reversed(memory_context[-3:]):
            last_sql = mem.get("sql", "")
            table_match = re.search(r"FROM\s+(\w+)", last_sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1).upper()
                metadata = schema_metadata.get(table_name, {})
                if metadata:
                    logger.debug(f"Inferred table {table_name} from memory context")
                    break
    if not table_name:
        logger.error("Could not determine table for prompt")
        raise Exception("❌ Could not determine table for prompt")

    # Ensure metadata is valid
    metadata = schema_metadata.get(table_name.split()[0], {})  # Handle JOIN cases
    if not metadata and rag_data:
        for rag_table, rag_meta in rag_data.items():
            if rag_table.upper() == table_name.split()[0]:
                metadata = rag_meta
                logger.debug(f"Using rag_data metadata for table: {table_name}")
                break
    if not metadata:
        logger.error(f"No metadata found for table: {table_name}")
        raise Exception(f"No metadata found for table: {table_name}")

    table_name_upper = table_name
    columns_meta = metadata.get("columns", {})
    fields = extract_entities(prompt)

    if not applied_business_terms:
        logger.warning(f"No business terms matched for prompt: {prompt}")

    # Detect aggregation
    force_count = any(kw in prompt_lower for kw in ["how many", "number of", "count of"])
    force_sum = any(kw in prompt_lower for kw in ["sum of", "total"])
    if force_count:
        agg_func = "COUNT"
        agg_col = None
    elif force_sum:
        agg_func = "SUM"
        agg_col = None
    else:
        try:
            agg_func, agg_col = detect_aggregation(prompt, columns_meta)
        except Exception:
            agg_func, agg_col = None, None
        logger.debug(f"Aggregation detected: {agg_func} on column {agg_col}")

    # Fallback column for COUNT and SUM
    if agg_func in ["COUNT", "SUM"]:
        if not agg_col:
            if agg_func == "COUNT":
                agg_col = next(
                    (col for col, meta in columns_meta.items()
                     if isinstance(meta, dict) and meta.get("type") not in ["boolean"]),
                    "APPL_NB"
                )
                logger.debug(f"Selected COUNT column: {agg_col}")
            elif agg_func == "SUM":
                for col, meta in columns_meta.items():
                    if isinstance(meta, dict) and meta.get("type") == "numeric":
                        if col.lower() in prompt_lower or meta.get("desc", "").lower() in prompt_lower:
                            agg_col = col
                            break
                agg_col = agg_col or next(
                    (col for col, meta in columns_meta.items()
                     if isinstance(meta, dict) and meta.get("type") == "numeric"),
                    None
                )
                logger.debug(f"Selected SUM column: {agg_col}")

    # Handle percentage logic
    if agg_func == "PERCENTAGE":
        if not percentage_condition:
            # Try business terms first
            for key, rule in business_terms.items():
                negated = "non " + key in prompt_lower or "not " + key in prompt_lower
                term_match = "non " + key if "non " + key in prompt_lower else "not " + key if "not " + key in prompt_lower else key
                if term_match in prompt_lower and rule["table"].upper() == table_name.split()[0]:
                    agg_col = rule["column"].upper()
                    val = rule["value"]
                    val = str(val).upper() if isinstance(val, bool) or val in ["0", "1"] else f"'{val}'"
                    if negated and key in ["eligible", "non-eligible", "approved", "rejected", "booked", "declined"]:
                        if val == "'1'":
                            val = "'0'"
                        elif val == "'0'":
                            val = "'1'"
                        else:
                            stripped_val = val.strip("'")
                            val = f"'Not {stripped_val}'"
                    percentage_condition = f"{agg_col} = {val}"
                    where_clauses.append(percentage_condition)  # Business term conditions go to WHERE
                    logger.debug(f"Selected PERCENTAGE condition from business term: {percentage_condition}")
                    break
        # If no business term or multiple conditions, try comparative/direct filters
        if not percentage_condition or " and " in prompt_lower:
            comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
            direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
            all_filters = comparative_filters + direct_filters
            if all_filters:
                percentage_condition = " AND ".join(all_filters) if all_filters else percentage_condition
                logger.debug(f"Percentage condition from filters: {percentage_condition}")
            elif not percentage_condition:
                logger.error("Could not infer condition for percentage query")
                raise Exception("❌ Could not infer condition for percentage query")

    # Date range logic
    inferred_from, inferred_to = parse_date_range_from_prompt(prompt)
    from_dt = parser.parse(from_date).strftime("%Y-%m-%d") if from_date else inferred_from
    to_dt = parser.parse(to_date).strftime("%Y-%m-%d") if to_date else inferred_to
    date_cols = [col for col, meta in columns_meta.items()
                 if isinstance(meta, dict) and meta.get("type") in ["date", "timestamp"]]
    date_col = date_cols[0].upper() if date_cols else None
    if (from_dt or to_dt) and date_col:
        if from_dt and to_dt:
            where_clauses.append(f"{date_col} BETWEEN '{from_dt}' AND '{to_dt}'")
        else:
            if from_dt:
                where_clauses.append(f"{date_col} >= '{from_dt}'")
            if to_dt:
                where_clauses.append(f"{date_col} <= '{to_dt}'")
        logger.debug(f"Applied date filter: {date_col} from {from_dt} to {to_dt}")

    # Extract additional filters for non-percentage queries or additional conditions
    try:
        comparative_filters, filtered_columns = extract_comparative_filters(prompt, columns_meta)
        direct_filters = extract_direct_column_filters(prompt, columns_meta, filtered_columns=filtered_columns)
        additional_filters = comparative_filters + direct_filters
        additional_filters = list(dict.fromkeys(additional_filters))  # Remove duplicates
        if agg_func != "PERCENTAGE":
            where_clauses += additional_filters
            logger.debug(f"Applied filters for non-percentage query: {additional_filters}")
        elif agg_func == "PERCENTAGE" and percentage_condition and not percentage_over_match:
            # Exclude percentage_condition from where_clauses
            percentage_conditions = set(percentage_condition.split(" AND "))
            additional_filters = [f for f in additional_filters if f not in percentage_conditions]
            if additional_filters:
                where_clauses += additional_filters
                logger.debug(f"Additional filters for PERCENTAGE query: {additional_filters}")
    except Exception as e:
        logger.error(f"Filter extraction failed: {str(e)}")
        raise Exception(f"❌ Filter extraction failed: {str(e)}")

    # Build aggregation query
    if agg_func:
        try:
            if agg_func == "PERCENTAGE" and percentage_denominator_condition:
                # Custom percentage query for "term1 over term2"
                query = f"SELECT ROUND(100.0 * COUNT(CASE WHEN {percentage_condition} THEN 1 END) / NULLIF(COUNT(CASE WHEN {percentage_denominator_condition} THEN 1 END), 0), 2) AS percentage_result FROM {table_name_upper}"
            else:
                query = build_aggregation_query(agg_func, agg_col, table_name_upper, prompt, columns_meta, percentage_condition)
            if where_clauses:
                where_clause = " WHERE " + " AND ".join(where_clauses)
                query = re.sub(r"\bWHERE\b.*?(LIMIT|$)", where_clause, query, flags=re.IGNORECASE) or query + where_clause
            if "LIMIT" not in query.upper():
                limit = extract_limit_from_prompt(prompt) or 50
                query += f" LIMIT {limit}"
            logger.info(f"Generated aggregation SQL: {query}")
            return query
        except Exception as e:
            logger.error(f"Aggregation query failed: {str(e)}")
            raise Exception(f"❌ Aggregation query failed: {str(e)}")

    # Default SELECT query
    selected_cols = [col.upper() for col in columns_meta.keys()]
    query = f"SELECT {', '.join(selected_cols)} FROM {table_name_upper}"
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    else:
        logger.warning(f"No WHERE clauses generated for prompt: {prompt}")
    query += f" LIMIT {limit or extract_limit_from_prompt(prompt) or 50}"
    logger.info(f"Generated SQL: {query}")
    return query