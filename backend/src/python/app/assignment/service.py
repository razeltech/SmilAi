import uuid
from datetime import datetime
from sqlite3 import Connection
from typing import List, Dict, Any, Optional

def create_assignment(
    db: Connection,
    subject_id: str,
    title: str,
    description: str,
    rubric: str,
    due_date: str,
    status: str = "draft"
) -> str:
    assignment_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    published_at = now if status == "published" else None
    
    db.execute(
        """
        INSERT INTO assignments (
            id, subject_id, title, description, rubric, due_date, status, created_at, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (assignment_id, subject_id, title, description, rubric, due_date, status, now, published_at)
    )
    return assignment_id

def get_assignment(db: Connection, assignment_id: str) -> Optional[Dict[str, Any]]:
    row = db.execute(
        "SELECT * FROM assignments WHERE id = ? AND deleted_at IS NULL", 
        (assignment_id,)
    ).fetchone()
    return row

def update_assignment(
    db: Connection,
    assignment_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    rubric: Optional[str] = None,
    due_date: Optional[str] = None,
    status: Optional[str] = None
):
    updates = []
    params = []
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if rubric is not None:
        updates.append("rubric = ?")
        params.append(rubric)
    if due_date is not None:
        updates.append("due_date = ?")
        params.append(due_date)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
        if status == "published":
            updates.append("published_at = ?")
            params.append(datetime.utcnow().isoformat())
        
    if not updates:
        return
        
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(assignment_id)
    
    query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
    db.execute(query, tuple(params))

def delete_assignment(db: Connection, assignment_id: str):
    db.execute(
        "UPDATE assignments SET deleted_at = ?, status = 'archived' WHERE id = ?",
        (datetime.utcnow().isoformat(), assignment_id)
    )
