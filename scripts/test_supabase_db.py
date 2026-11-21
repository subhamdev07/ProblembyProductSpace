"""
Check Both Local SQLite and Cloud Supabase Databases
"""

import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("1. LOCAL SQLITE DATABASE (data/curriculum.db)")
print("=" * 70)
if os.path.exists("data/curriculum.db"):
    sqlite_conn = sqlite3.connect("data/curriculum.db")
    cur = sqlite_conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Status: ONLINE | Tables Count: {len(tables)}")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cur.fetchone()[0]
        print(f"  - {t:30}: {cnt} rows")
    sqlite_conn.close()
else:
    print("Status: NOT FOUND")

print("\n" + "=" * 70)
print("2. CLOUD SUPABASE POSTGRESQL DATABASE")
print("=" * 70)
db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("Status: SUPABASE_DB_URL NOT CONFIGURED")
else:
    try:
        pg_conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = pg_conn.cursor()
        cur.execute("SELECT current_database(), current_user, version();")
        db_info = cur.fetchone()
        print(f"Status: ONLINE & CONNECTED")
        print(f"Database: {db_info[0]} | User: {db_info[1]}")
        print(f"PostgreSQL Version: {db_info[2][:50]}...")
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
        pg_tables = [t[0] for t in cur.fetchall()]
        print(f"Tables in 'public' schema: {len(pg_tables)}")
        if pg_tables:
            for pt in pg_tables:
                print(f"  - {pt}")
        else:
            print("  (Currently 0 tables in Supabase public schema. Cloud migration pending.)")
        cur.close()
        pg_conn.close()
    except Exception as e:
        print(f"Status: CONNECTION FAILED: {e}")
print("=" * 70)
