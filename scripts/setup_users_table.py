import sqlite3

def setup_users():
    conn = sqlite3.connect('data/curriculum.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        grade INTEGER DEFAULT 10,
        password_hash TEXT NOT NULL,
        avatar TEXT,
        school TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    demo_users = [
        ('STU-001', 'Aarav Sharma', 'aarav@bodhai.edu', 'student', 10, 'password123', 'AS', 'Delhi Public School, R.K. Puram'),
        ('STU-002', 'Priya Patel', 'priya@bodhai.edu', 'student', 10, 'password123', 'PP', 'Kendriya Vidyalaya, IIT Powai'),
        ('STU-003', 'Rohan Verma', 'rohan@bodhai.edu', 'student', 10, 'password123', 'RV', "St. Xavier's High School, Mumbai"),
        ('TCH-001', 'Dr. Sunita Rao', 'sunita@bodhai.edu', 'teacher', 10, 'password123', 'SR', 'National Science Teachers Association'),
        ('TCH-002', 'Dr. Sunita Rao', 'teacher@bodhai.edu', 'teacher', 10, 'password123', 'SR', 'National Science Teachers Association'),
    ]

    for u in demo_users:
        c.execute('''
        INSERT INTO users (user_id, name, email, role, grade, password_hash, avatar, school)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            role=excluded.role,
            grade=excluded.grade,
            password_hash=excluded.password_hash,
            avatar=excluded.avatar,
            school=excluded.school
        ''', u)

    c.execute("DELETE FROM students WHERE student_id LIKE 'TCH%';")
    c.execute("DELETE FROM students WHERE student_id LIKE 'STU-TEST%';")
    c.execute("DELETE FROM students WHERE student_id LIKE 'STU-EVAL%';")

    students = [
        ('STU-001', 'Aarav Sharma', 10),
        ('STU-002', 'Priya Patel', 10),
        ('STU-003', 'Rohan Verma', 10),
    ]
    for s in students:
        c.execute("INSERT OR REPLACE INTO students (student_id, name, grade) VALUES (?, ?, ?);", s)

    conn.commit()
    print("Users successfully seeded:")
    for r in c.execute("SELECT user_id, name, email, role, grade FROM users;").fetchall():
        print("  ", r)

    print("Students verified:")
    for r in c.execute("SELECT student_id, name, grade FROM students;").fetchall():
        print("  ", r)

    conn.close()

if __name__ == '__main__':
    setup_users()
