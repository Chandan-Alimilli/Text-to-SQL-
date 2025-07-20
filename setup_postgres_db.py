import psycopg2

# ✅ Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="railway",
    user="postgres",
    password="rodbbXXAtvbTseqxaaGHxGMkLWNaRawl",
    host="crossover.proxy.rlwy.net",
    port="48319"
)

cursor = conn.cursor()

sql_file_path = "final_auto_finance_cleaned.sql"

# ✅ Read SQL script
with open(sql_file_path, "r", encoding="utf-8") as f:
    sql = f.read()

statements = sql.strip().split(";")

for idx, statement in enumerate(statements):
    statement = statement.strip()
    if statement:
        try:
            cursor.execute(statement + ";")
            conn.commit()  # ✅ Commit each valid statement
        except Exception as e:
            print(f"⚠️ Error in statement {idx + 1}:\n{statement[:300]}...\n{e}\n")
            conn.rollback()  # ❗ Rollback this failed statement

cursor.close()
conn.close()

print("✅ Script executed with error handling.")
