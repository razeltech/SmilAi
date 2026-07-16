from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from ...database.connection import get_db
from ...assignment.service import update_assignment

router = APIRouter(tags=["Admin - Assignments"])

class AssignmentPostRequest(BaseModel):
    subjectId: str
    title: str
    description: str
    rubric: str
    dueDate: str

class AssignmentPatchRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rubric: Optional[str] = None
    dueDate: Optional[str] = None
    status: Optional[str] = None

class OverrideGradeRequest(BaseModel):
    score: int
    feedback: str

@router.get("/assignments")
def get_all_assignments(db: Connection = Depends(get_db)):
    """Returns all active assignments across all subjects."""
    rows = db.execute("SELECT * FROM assignments WHERE deleted_at IS NULL ORDER BY due_date DESC").fetchall()
    return [
        {
            "id": r["id"], "subjectId": r["subject_id"], "title": r["title"],
            "description": r["description"], "rubric": r["rubric"], "dueDate": r["due_date"]
        }
        for r in rows
    ]

@router.get("/subjects/{subjectId}/assignments")
def get_subject_assignments(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all active assignments for a subject."""
    rows = db.execute(
        "SELECT * FROM assignments WHERE subject_id = ? AND deleted_at IS NULL ORDER BY due_date DESC",
        (subjectId,)
    ).fetchall()
    return [
        {
            "id": r["id"],
            "subjectId": r["subject_id"],
            "title": r["title"],
            "description": r["description"],
            "rubric": r["rubric"],
            "dueDate": r["due_date"]
        }
        for r in rows
    ]

@router.post("/assignments")
def create_assignment(req: AssignmentPostRequest, db: Connection = Depends(get_db)):
    """Creates a new programming assignment."""
    assign_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO assignments (id, subject_id, title, description, rubric, due_date) VALUES (?, ?, ?, ?, ?, ?)",
        (assign_id, req.subjectId, req.title, req.description, req.rubric, req.dueDate)
    )
    db.commit()
    return {
        "id": assign_id,
        "subjectId": req.subjectId,
        "title": req.title,
        "description": req.description,
        "rubric": req.rubric,
        "dueDate": req.dueDate
    }

@router.patch("/assignments/{id}")
def edit_assignment(id: str, req: AssignmentPatchRequest, db: Connection = Depends(get_db)):
    """Updates an existing assignment."""
    update_assignment(db, id, req.title, req.description, req.rubric, req.dueDate, req.status)
    db.commit()
    return {"message": "Success"}

@router.delete("/assignments/{id}")
def delete_assignment(id: str, db: Connection = Depends(get_db)):
    """Soft deletes an assignment."""
    now_str = datetime.utcnow().isoformat()
    cursor = db.execute(
        "UPDATE assignments SET deleted_at = ? WHERE id = ?",
        (now_str, id)
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Success"}

# Grade Overrides & Submissions
@router.get("/subjects/{subjectId}/submissions")
def get_subject_submissions(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all code submissions for assignments in a subject."""
    rows = db.execute("""
        SELECT sub.*, a.title AS assignment_title 
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        WHERE a.subject_id = ? AND a.deleted_at IS NULL
        ORDER BY sub.submitted_at DESC
    """, (subjectId,)).fetchall()
    return [
        {
            "id": r["id"],
            "assignmentId": r["assignment_id"],
            "studentId": r["student_id"],
            "fileName": r["file_name"],
            "score": r["score"],
            "feedback": r["feedback"],
            "teacherOverride": r["teacher_override"],
            "submittedAt": r["submitted_at"],
            "assignmentTitle": r.get("assignment_title", "")
        }
        for r in rows
    ]

@router.post("/submissions/{submissionId}/override")
def override_grade(submissionId: str, req: OverrideGradeRequest, db: Connection = Depends(get_db)):
    """Allows teachers to override submission grades and feedback."""
    cursor = db.execute(
        "UPDATE submissions SET score = ?, feedback = ?, teacher_override = 1 WHERE id = ?",
        (req.score, req.feedback, submissionId)
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Success", "score": req.score, "feedback": req.feedback}
