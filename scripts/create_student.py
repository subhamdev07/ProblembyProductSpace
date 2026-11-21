"""
BodhAI (बोध AI) — Standalone Fresh Student Account Provisioner
Allows creating new, completely fresh student accounts in the BodhAI database
without modifying any application source code (src/ or frontend/).
"""

import sys
import os
import argparse
import sqlite3
from typing import Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "curriculum.db")


def get_next_student_id(conn: sqlite3.Connection) -> str:
    """Finds the next incremental STU-XXX identifier."""
    cursor = conn.cursor()
    cursor.execute("SELECT student_id FROM students WHERE student_id LIKE 'STU-%';")
    rows = cursor.fetchall()
    
    max_num = 0
    for (sid,) in rows:
        parts = sid.split("-")
        if len(parts) >= 2 and parts[1].isdigit():
            num = int(parts[1])
            if num > max_num:
                max_num = num
                
    next_num = max_num + 1
    return f"STU-{next_num:03d}"


def get_initials(name: str) -> str:
    """Generates a 2-character uppercase avatar initial from a full name."""
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) >= 2:
        return parts[0][:2].upper()
    return "ST"


def create_fresh_student(
    name: str,
    email: str,
    password: str = "password123",
    grade: int = 10,
    school: str = "Delhi Public School, R.K. Puram",
    custom_id: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Creates a new student profile in `students` and `users` tables.
    Guarantees that the new student starts completely fresh with 0 prior history.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database file not found at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()

        # Check if email is already taken
        cursor.execute("SELECT user_id, name FROM users WHERE LOWER(email) = LOWER(?);", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise ValueError(f"Email '{email}' is already registered to user '{existing_user[1]}' ({existing_user[0]}).")

        # Determine student ID
        student_id = custom_id or get_next_student_id(conn)
        avatar = get_initials(name)

        # 1. Insert into students table
        cursor.execute(
            "INSERT INTO students (student_id, name, grade) VALUES (?, ?, ?);",
            (student_id, name.strip(), grade)
        )

        # 2. Insert into users table
        cursor.execute(
            """
            INSERT INTO users (user_id, name, email, role, grade, password_hash, avatar, school)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (student_id, name.strip(), email.strip().lower(), "student", grade, password, avatar, school.strip())
        )

        # 3. Clean any accidental historical rows for this student ID to ensure 100% fresh start
        cursor.execute("DELETE FROM learner_concept_mastery WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM student_misconceptions WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM spaced_repetition_schedules WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM remediation_records WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM assessments WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM student_answers WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM examination_sessions WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM examination_answers WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM examination_results WHERE student_id = ?;", (student_id,))
        cursor.execute("DELETE FROM student_activity_logs WHERE student_id = ?;", (student_id,))

        conn.commit()
        return student_id, name.strip(), email.strip().lower()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Create a fresh student account in BodhAI.")
    parser.add_argument("--name", type=str, help="Full Name of the student (e.g. 'Aanya Gupta')")
    parser.add_argument("--email", type=str, help="Email address (e.g. 'aanya@bodhai.edu')")
    parser.add_argument("--password", type=str, default="password123", help="Password (default: 'password123')")
    parser.add_argument("--grade", type=int, default=10, help="Class/Grade level (default: 10)")
    parser.add_argument("--school", type=str, default="Delhi Public School, R.K. Puram", help="School name")
    parser.add_argument("--id", type=str, default=None, help="Custom Student ID (e.g. 'STU-005')")

    args = parser.parse_args()

    name = args.name
    email = args.email

    # Interactive prompt fallback if run without arguments
    if not name or not email:
        print("\n" + "=" * 65)
        print("  BodhAI — Create Fresh Student Account")
        print("=" * 65)
        if not name:
            name = input("  Enter Student Full Name: ").strip()
        if not email:
            email = input("  Enter Student Email: ").strip()

    if not name or not email:
        print("Error: Both Student Name and Email are required.")
        sys.exit(1)

    try:
        student_id, student_name, student_email = create_fresh_student(
            name=name,
            email=email,
            password=args.password,
            grade=args.grade,
            school=args.school,
            custom_id=args.id
        )

        print("\n" + "=" * 65)
        print("  🎉 FRESH STUDENT ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 65)
        print(f"  • Student ID : {student_id}")
        print(f"  • Full Name  : {student_name}")
        print(f"  • Email      : {student_email}")
        print(f"  • Password   : {args.password}")
        print(f"  • Grade      : Class {args.grade}")
        print(f"  • School     : {args.school}")
        print("  • Starting State: 100% Fresh (0% Mastery, 0 Diagnostic, 0 Exams)")
        print("-" * 65)
        print("  To log in now:")
        print(f"  1. Go to: http://127.0.0.1:8000/login")
        print(f"  2. Select 'Student' role")
        print(f"  3. Email: {student_email}")
        print(f"  4. Password: {args.password}")
        print("=" * 65 + "\n")

    except Exception as e:
        print(f"\n❌ Failed to create student account: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
