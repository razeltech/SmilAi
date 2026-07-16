import sqlite3
import os
from contextlib import contextmanager

# Default to local db if env var is missing
DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "database", "smilai.db"))
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "database", "schema.sql")

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

def ensure_column(conn, table: str, column: str, definition: str):
    """Safely adds a column to a table if it does not already exist."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table});")
    rows = cursor.fetchall()
    columns = []
    for r in rows:
        if isinstance(r, dict):
            columns.append(r.get("name"))
        else:
            columns.append(r[1])
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition};")
        print(f"Migration: Added column '{column}' to table '{table}'.")

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
        
        # Run database migrations for Platform v1.1 / Milestone A columns
        ensure_column(conn, "documents", "status", "TEXT CHECK(status IN ('pending', 'approved', 'archived')) NOT NULL DEFAULT 'approved'")
        ensure_column(conn, "assessments", "deleted_at", "TEXT")
        ensure_column(conn, "assignments", "deleted_at", "TEXT")
        
        # Platform v1.1 migrations
        ensure_column(conn, "subjects", "category", "TEXT CHECK(category IN ('GENERAL', 'PROGRAMMING', 'SCIENCE', 'LANGUAGE', 'MEDICAL')) NOT NULL DEFAULT 'GENERAL'")
        ensure_column(conn, "subjects", "supports_projects", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "subjects", "is_active", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(conn, "subjects", "updated_at", "TEXT")
        ensure_column(conn, "subjects", "deleted_at", "TEXT")
        
        ensure_column(conn, "documents", "processed_at", "TEXT")
        
        ensure_column(conn, "assessments", "status", "TEXT CHECK(status IN ('draft', 'published', 'archived')) NOT NULL DEFAULT 'published'")
        ensure_column(conn, "assessments", "published_at", "TEXT")
        ensure_column(conn, "assessments", "updated_at", "TEXT")
        
        ensure_column(conn, "questions", "explanation", "TEXT")
        ensure_column(conn, "questions", "difficulty", "TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')) NOT NULL DEFAULT 'Medium'")
        ensure_column(conn, "questions", "updated_at", "TEXT")
        
        ensure_column(conn, "assignments", "status", "TEXT CHECK(status IN ('draft', 'published', 'archived')) NOT NULL DEFAULT 'published'")
        ensure_column(conn, "assignments", "created_at", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "assignments", "updated_at", "TEXT")
        ensure_column(conn, "assignments", "published_at", "TEXT")
        
        # Backfill existing assignments created_at to preserve backward compatibility
        conn.execute("UPDATE assignments SET created_at = due_date WHERE created_at = ''")
        
        # Seed default data if none exists
        org = conn.execute("SELECT id FROM organizations LIMIT 1").fetchone()
        if not org:
            import uuid
            try:
                import bcrypt
                def hash_password(password: str) -> str:
                    salt = bcrypt.gensalt()
                    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            except ImportError:
                def hash_password(password: str) -> str:
                    # Insecure fallback ONLY if bcrypt is missing (e.g. lightweight install)
                    return f"mock_hash_{password}"
                
            org_id = "org_1"
            conn.execute("INSERT INTO organizations (id, name) VALUES (?, ?)", (org_id, "SmilAI Demo School"))
            
            pwd = hash_password("password")
            student_id = "student_rahul"
            teacher_id = "teacher_sharma"
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (student_id, "Rahul Kumar", "rahul@school.org", pwd, "student", org_id))
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (teacher_id, "Mr. Sharma", "sharma@school.org", pwd, "teacher", org_id))
            conn.execute("INSERT INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), "School Administrator", "admin@school.org", pwd, "admin", org_id))
            
            # Seed a default subject for Rahul and Sharma using a deterministic ID
            grade_band_id = "grade_10"
            conn.execute("INSERT INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)", (grade_band_id, org_id, "Grade 10"))
            
            subject_id = "math_101"
            conn.execute("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)", (subject_id, org_id, grade_band_id, "Advanced Mathematics", teacher_id))
            
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
