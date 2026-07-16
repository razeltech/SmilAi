from fastapi import APIRouter, Depends
from sqlite3 import Connection
from pydantic import BaseModel

from ...database.connection import get_db
from ...subject.service import enroll_student, unenroll_student

router = APIRouter(tags=["Admin - Enrollments"])

class SubjectEnrollRequest(BaseModel):
    userId: str

@router.post("/subjects/{subjectId}/enroll")
def enroll_user(subjectId: str, req: SubjectEnrollRequest, db: Connection = Depends(get_db)):
    """Enrolls a student in a subject."""
    enroll_student(db, subjectId, req.userId)
    db.commit()
    return {"message": "Success"}

@router.delete("/subjects/{subjectId}/enroll/{userId}")
def unenroll_user(subjectId: str, userId: str, db: Connection = Depends(get_db)):
    """Unenrolls a student from a subject."""
    unenroll_student(db, subjectId, userId)
    db.commit()
    return {"message": "Success"}
