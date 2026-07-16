import pytest
from app.database.connection import init_db
import sqlite3
import os

def test_startup_db_initialization(tmp_path, monkeypatch):
    test_db = tmp_path / "startup_test.db"
    
    # Overwrite the actual module variable since it's already loaded
    import app.database.connection
    monkeypatch.setattr(app.database.connection, "DB_PATH", str(test_db))
    
    # Run initialization
    init_db()
    
    # Verify tables created
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    conn.close()
    
    table_names = [t[0] for t in tables]
    assert "users" in table_names
    assert "organizations" in table_names
    assert "subjects" in table_names
    assert "documents" in table_names
    assert "concept_mastery" in table_names
    
def test_startup_profiles():
    from app.core.config.env import _mode
    assert _mode in ["lite", "standard", "pro"]
