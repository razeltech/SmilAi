import sqlite3
import os
from contextlib import contextmanager

# Default to local db if env var is missing
DB_PATH = os.environ.get("SQLITE_DB_PATH", "./database/smilai.db")
SCHEMA_PATH = "./database/schema.sql"

def dict_factory(cursor, row):
    """Returns DB rows as dictionaries instead of tuples for clean JSON serialization."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Create and return a new SQLite connection with Foreign Keys enforced."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database using the unified schema.sql file."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"Warning: Schema file not found at {SCHEMA_PATH}")
        return

    with open(SCHEMA_PATH, 'r') as f:
        schema_script = f.read()

    conn = get_db_connection()
    try:
        conn.executescript(schema_script)
        
        # Seed default data if none exists
        org = conn.execute("SELECT id FROM organizations LIMIT 1").fetchone()
        if not org:
            import uuid
            import bcrypt
            
            def hash_password(password: str) -> str:
                salt = bcrypt.gensalt()
                return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
            org_id = str(uuid.uuid4())
            conn.execute("INSERT INTO organizations (id, name) VALUES (?, ?)", (org_id, "SmilAI Demo School"))
            
            pwd = hash_password("password")
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), "Rahul Kumar", "rahul@school.org", pwd, "student", org_id))
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), "Mr. Sharma", "sharma@school.org", pwd, "teacher", org_id))
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), "School Administrator", "admin@school.org", pwd, "admin", org_id))
            
            # Seed a default subject for Rahul and Sharma
            grade_band_id = str(uuid.uuid4())
            conn.execute("INSERT INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)", (grade_band_id, org_id, "Grade 1"))
            
            teacher_id = conn.execute("SELECT id FROM users WHERE email = 'sharma@school.org'").fetchone()["id"]
            subject_id = str(uuid.uuid4())
            conn.execute("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)", (subject_id, org_id, grade_band_id, "Mathematics", teacher_id))
            
            student_id = conn.execute("SELECT id FROM users WHERE email = 'rahul@school.org'").fetchone()["id"]
            conn.execute("INSERT INTO enrollments (user_id, subject_id) VALUES (?, ?)", (student_id, subject_id))
            
            print("Database seeded with demo accounts and sample subjects.")

        conn.commit()
        print("Database schema initialized successfully.")
    except Exception as e:
        print(f"Error initializing database schema: {e}")
    finally:
        conn.close()

def get_db():
    """FastAPI Dependency for database connections."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
