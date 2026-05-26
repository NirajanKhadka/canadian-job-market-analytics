# test.py
import psycopg2

conn = psycopg2.connect(
    host="aws-1-us-east-1.pooler.supabase.com",
    port=5432,
    dbname="postgres",
    user="postgres.stcbnxrncrdrutkfoegn",
    password="pwd@Supabase99",
    sslmode="require"
)
print("✅ Connected via Supabase pooler!")
conn.close()