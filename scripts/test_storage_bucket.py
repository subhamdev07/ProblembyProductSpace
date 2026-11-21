import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
cur = conn.cursor()
try:
    cur.execute("INSERT INTO storage.buckets (id, name, public) VALUES ('curriculum-sources', 'curriculum-sources', false) ON CONFLICT (id) DO NOTHING;")
    conn.commit()
    print("Bucket 'curriculum-sources' created/verified in Supabase Storage!")
    cur.execute("SELECT id, name, public FROM storage.buckets;")
    print("Buckets in Supabase:", cur.fetchall())
except Exception as e:
    print("Bucket error:", e)
cur.close()
conn.close()
