import psycopg2

# Connection URL
conn_url = "postgresql://postgres:JpqdXMBPXZqftuMThUgUBXnpzPgsXVOd@tramway.proxy.rlwy.net:44410/railway"

# Read schema.sql
with open("schema.sql", "r") as f:
    schema_sql = f.read()

try:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(conn_url)
    conn.autocommit = True
    cursor = conn.cursor()

    # Execute the SQL script
    cursor.execute(schema_sql)
    print("✅ schema.sql pushed successfully to Railway PostgreSQL.")

    cursor.close()
    conn.close()
except Exception as e:
    print("❌ Error occurred:", e)
