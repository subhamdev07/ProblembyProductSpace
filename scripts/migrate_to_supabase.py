"""
BodhAI — Supabase PostgreSQL Cloud Migration Script
Connects to Supabase using SUPABASE_DB_URL, applies schema DDL,
and synchronizes verified curriculum and learner data from SQLite.
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Ensure root workspace is accessible
sys.path.insert(0, os.path.abspath("."))
load_dotenv()


TABLE_ORDER = [
    # P0 Foundation
    "source_documents",
    "academic_sessions",
    "subjects",
    "curricula",
    "units",
    "chapters",
    "topics",
    "subtopics",
    "learning_outcomes",
    "curriculum_mappings",
    "source_citations",
    # P1 Concept Graph
    "concepts",
    "concept_relationships",
    "concept_provenance",
    # P2 Question Bank
    "questions",
    "question_concept_mappings",
    "question_learning_outcome_mappings",
    # P3 Assessment & Learner Model
    "students",
    "assessments",
    "assessment_questions",
    "student_answers",
    "learner_concept_mastery",
    "student_misconceptions",
    # P4 Remediation, Spaced Repetition & RAG
    "spaced_repetition_schedules",
    "remediation_records",
    "curriculum_embeddings",
]


def load_schema_ddl(schema_path: str = "src/storage/schema.sql") -> list[str]:
    with open(schema_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Filter out comments and PRAGMA lines
    cleaned_lines = []
    for line in content.splitlines():
        line_strip = line.strip()
        if line_strip.startswith("--") or line_strip.upper().startswith("PRAGMA"):
            continue
        cleaned_lines.append(line)

    cleaned_content = "\n".join(cleaned_lines)

    # Split into statements
    statements = []
    for stmt in cleaned_content.split(";"):
        stmt_clean = stmt.strip()
        if not stmt_clean:
            continue
        statements.append(stmt_clean + ";")
    return statements


def migrate():
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("[ERROR] SUPABASE_DB_URL is not set in .env")
        sys.exit(1)

    sqlite_path = "data/curriculum.db"
    if not os.path.exists(sqlite_path):
        print(f"[ERROR] SQLite database not found at {sqlite_path}")
        sys.exit(1)

    print("=" * 70)
    print("  BodhAI — Supabase Cloud Database Deployment")
    print("=" * 70)

    # 1. Connect to Supabase PostgreSQL
    try:
        pg_conn = psycopg2.connect(db_url, connect_timeout=10)
        pg_conn.autocommit = False
        print("[1/4] Connected to Supabase PostgreSQL successfully.")
    except Exception as e:
        print(f"[ERROR] Connection to Supabase failed: {e}")
        sys.exit(1)

    pg_cur = pg_conn.cursor()

    # Try enabling pgvector extension
    try:
        pg_cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        pg_conn.commit()
        print("      -> pgvector extension enabled successfully.")
    except Exception as e:
        pg_conn.rollback()
        print(f"      -> [INFO] pgvector extension note: {e}")

    # 2. Execute DDL Schema Statements
    print("[2/4] Applying Relational Schema DDL...")
    ddl_statements = load_schema_ddl()
    applied_count = 0
    for stmt in ddl_statements:
        try:
            pg_cur.execute(stmt)
            applied_count += 1
        except Exception as e:
            pg_conn.rollback()
            print(f"[ERROR] Failed applying DDL statement:\n{stmt[:100]}...\nReason: {e}")
            pg_conn.close()
            sys.exit(1)

    pg_conn.commit()
    print(f"      -> Successfully applied {applied_count} DDL statements (tables & indexes).")

    # Ensure pgvector column exists on curriculum_embeddings in Supabase
    try:
        pg_cur.execute("ALTER TABLE curriculum_embeddings ADD COLUMN IF NOT EXISTS embedding vector(2048);")
        pg_cur.execute("ALTER TABLE student_misconceptions ADD COLUMN IF NOT EXISTS evidence_text TEXT;")
        pg_conn.commit()
        print("      -> pgvector column 'embedding vector(2048)' verified on curriculum_embeddings.")
    except Exception as e:
        pg_conn.rollback()
        print(f"      -> Note on vector column: {e}")

    # 3. Synchronize Data from SQLite
    print("[3/4] Synchronizing verified data from local SQLite to Supabase...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    sync_results = {}

    for table in TABLE_ORDER:
        try:
            sqlite_cur.execute(f"SELECT * FROM {table};")
            rows = sqlite_cur.fetchall()
            if not rows:
                sync_results[table] = 0
                continue

            col_names = [col[0] for col in sqlite_cur.description]
            cols_clause = sql.SQL(", ").join([sql.Identifier(c) for c in col_names])
            vals_clause = sql.SQL(", ").join([sql.Placeholder() for _ in col_names])

            insert_query = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals}) ON CONFLICT DO NOTHING;").format(
                table=sql.Identifier(table),
                cols=cols_clause,
                vals=vals_clause
            )

            row_data = [tuple(r[c] for c in col_names) for r in rows]
            psycopg2.extras.execute_batch(pg_cur, insert_query, row_data)
            pg_conn.commit()
            sync_results[table] = len(row_data)
        except Exception as e:
            pg_conn.rollback()
            print(f"[WARNING] Table sync issue on '{table}': {e}")
            sync_results[table] = f"ERROR: {e}"

    sqlite_conn.close()

    # 4. Verify Tables in Supabase
    print("[4/4] Verifying Cloud Database Deployment...")
    pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
    deployed_tables = [t[0] for t in pg_cur.fetchall()]

    print("\n" + "=" * 70)
    print(f"  DEPLOYMENT SUMMARY: {len(deployed_tables)} Tables Created in Supabase Public Schema")
    print("=" * 70)
    print(f"  {'Table Name':<35} | {'Synced Rows':<12} | {'Status'}")
    print("  " + "-" * 65)

    for table in TABLE_ORDER:
        count = sync_results.get(table, 0)
        status = "DEPLOYED & SYNCED" if isinstance(count, int) and count > 0 else ("SCHEMA READY" if count == 0 else "WARNING")
        print(f"  {table:<35} | {str(count):<12} | {status}")

    print("=" * 70)
    print("  Supabase Cloud Database initialization and data migration complete!\n")

    pg_cur.close()
    pg_conn.close()


if __name__ == "__main__":
    import psycopg2.extras
    migrate()
