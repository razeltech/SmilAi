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
