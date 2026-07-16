from fastapi import APIRouter, Depends
from sqlite3 import Connection
from pydantic import BaseModel
from typing import Optional

from ...database.connection import get_db
from ...subject.service import (
    create_subject, 
    update_subject, 
    delete_subject, 
    get_subjects_list,
    get_grade_bands_list
)

router = APIRouter(tags=["Admin - Subjects"])

class SubjectPostRequest(BaseModel):
    orgId: str
    name: str
    teacherId: str
    gradeBandId: str
    category: str = "GENERAL"
    supportsProjects: int = 0
    isActive: int = 1

class SubjectPatchRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    supportsProjects: Optional[int] = None
    isActive: Optional[int] = None

@router.get("/grade-bands")
def get_grade_bands(db: Connection = Depends(get_db)):
    """Returns all grade bands."""
    return get_grade_bands_list(db)

@router.get("/subjects")
def get_subjects(userId: str = None, role: str = None, db: Connection = Depends(get_db)):
    """Returns subjects based on user role."""
    return get_subjects_list(db, userId, role)

@router.post("/subjects")
def add_subject(req: SubjectPostRequest, db: Connection = Depends(get_db)):
    """Creates a new subject."""
    subject_id = create_subject(
        db, req.orgId, req.gradeBandId, req.name, req.teacherId,
        req.category, req.supportsProjects, req.isActive
    )
    db.commit()
    return {"id": subject_id, "message": "Success"}

@router.patch("/subjects/{id}")
def patch_subject(id: str, req: SubjectPatchRequest, db: Connection = Depends(get_db)):
    """Updates a subject."""
    update_subject(
        db, id, req.name, req.category, req.supportsProjects, req.isActive
    )
    db.commit()
    return {"message": "Success"}

@router.delete("/subjects/{id}")
def remove_subject(id: str, db: Connection = Depends(get_db)):
    """Soft deletes a subject."""
    delete_subject(db, id)
    db.commit()
    return {"message": "Success"}
