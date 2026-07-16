import uuid
from datetime import datetime
from sqlite3 import Connection
from typing import List, Dict, Any, Optional

def create_subject(
    db: Connection,
    org_id: str,
    grade_band_id: str,
    name: str,
    teacher_id: str,
    category: str = "GENERAL",
    supports_projects: int = 0,
    is_active: int = 1
) -> str:
    subject_id = str(uuid.uuid4())
    db.execute(
        """
        INSERT INTO subjects (
            id, org_id, grade_band_id, name, teacher_id, category, supports_projects, is_active, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (subject_id, org_id, grade_band_id, name, teacher_id, category, supports_projects, is_active, datetime.utcnow().isoformat())
    )
    return subject_id

def get_subject(db: Connection, subject_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        "SELECT * FROM subjects WHERE id = ? AND deleted_at IS NULL", 
        (subject_id,)
    ).fetchone()
    return row

def update_subject(
    db: Connection,
    subject_id: str,
    name: Optional[str] = None,
    category: Optional[str] = None,
    supports_projects: Optional[int] = None,
    is_active: Optional[int] = None
):
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if supports_projects is not None:
        updates.append("supports_projects = ?")
        params.append(supports_projects)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(is_active)
        
    if not updates:
        return
        
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(subject_id)
    
    query = f"UPDATE subjects SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
    db.execute(query, tuple(params))

def delete_subject(db: Connection, subject_id: str):
    db.execute(
        "UPDATE subjects SET deleted_at = ?, is_active = 0 WHERE id = ?",
        (datetime.utcnow().isoformat(), subject_id)
    )

def enroll_student(db: Connection, subject_id: str, user_id: str):
    # Check if subject exists
    sub = get_subject(db, subject_id)
    if not sub:
        raise ValueError("Subject not found")
        
    # Idempotent insert
    db.execute(
        "INSERT OR IGNORE INTO enrollments (user_id, subject_id) VALUES (?, ?)",
        (user_id, subject_id)
    )

def unenroll_student(db: Connection, subject_id: str, user_id: str):
    db.execute(
        "DELETE FROM enrollments WHERE user_id = ? AND subject_id = ?",
        (user_id, subject_id)
    )
