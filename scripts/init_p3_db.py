"""
Initialize P3 Database Schema
Applies non-destructive schema extensions to data/curriculum.db
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
from src.storage.database import Database

def init_p3():
    db = Database("data/curriculum.db")
    db.init_db()
    with db.get_connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("P3 Tables Initialized:", [t for t in tables if t in ('students', 'assessments', 'assessment_questions', 'student_answers', 'learner_concept_mastery', 'student_misconceptions')])

        # Ensure demo student STU-001 exists
        conn.execute("""
        INSERT OR IGNORE INTO students (student_id, name, grade)
        VALUES ('STU-001', 'Aarav Sharma', 10);
        """)
        conn.commit()
        print("Demo student STU-001 verified.")

if __name__ == "__main__":
    init_p3()
