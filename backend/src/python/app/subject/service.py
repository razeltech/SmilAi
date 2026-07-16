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

def get_subjects_list(db: Connection, user_id: str = None, role: str = None) -> List[Dict[str, Any]]:
    if role == "admin" or not user_id:
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id, s.category, s.supports_projects, s.is_active,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
        """).fetchall()
    elif role == "teacher":
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id, s.category, s.supports_projects, s.is_active,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE s.teacher_id = ?
        """, (user_id,)).fetchall()
    else:
        # Student — return enrolled subjects
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id, s.category, s.supports_projects, s.is_active,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            JOIN enrollments e ON e.subject_id = s.id
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE e.user_id = ?
        """, (user_id,)).fetchall()

    return [
        {
            "id": s["id"],
            "orgId": s["org_id"],
            "gradeBandId": s["grade_band_id"],
            "name": s["name"],
            "teacherId": s["teacher_id"],
            "category": s.get("category", "GENERAL"),
            "supportsProjects": s.get("supports_projects", 0),
            "isActive": s.get("is_active", 1),
            "gradeBandName": s.get("grade_band_name", ""),
            "teacherName": s.get("teacher_name", "")
        }
        for s in subjects
    ]

def get_grade_bands_list(db: Connection) -> List[Dict[str, Any]]:
    rows = db.execute("SELECT * FROM grade_bands").fetchall()
    return [{"id": r["id"], "orgId": r["org_id"], "name": r["name"]} for r in rows]

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
