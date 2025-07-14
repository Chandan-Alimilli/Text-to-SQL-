import psycopg2

# ✅ PostgreSQL connection string
connection_string = "postgresql://postgres:HtNHeMLTYTFAzuPmSvXwgllgqmBNWdqW@caboose.proxy.rlwy.net:53958/railway"

# ✅ Extract components for psycopg2
conn = psycopg2.connect(
    dbname="railway",
    user="postgres",
    password="HtNHeMLTYTFAzuPmSvXwgllgqmBNWdqW",
    host="caboose.proxy.rlwy.net",
    port="53958"
)

cursor = conn.cursor()

# ✅ Path to your SQL schema file
sql_file_path = "auto_finance_full.sql"

# ✅ Read and execute SQL file
with open(sql_file_path, "r", encoding="utf-8") as f:
    sql = f.read()

# Split and execute statements safely
for statement in sql.strip().split(";"):
    if statement.strip():
        try:
            cursor.execute(statement + ";")
        except Exception as e:
            print(f"⚠️ Error executing: {statement[:100]}...\n{e}")

conn.commit()
cursor.close()
conn.close()

print("✅ PostgreSQL schema + data setup complete.")
