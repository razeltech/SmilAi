from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from ..database.connection import get_db
from ..learning_engine.analytics_service import generate_analytics, get_mastery_list
from ..learning_engine.revision_service import generate_revision_plan, get_revision_plan
from ..core.config import active_profile

router = APIRouter(tags=["Adaptive Learning"])

@router.get("/mastery/{student_id}")
def get_student_mastery(student_id: str, subjectId: str, db: Connection = Depends(get_db)):
    """Returns granular concept mastery list for UI (e.g. progress bars, dots)."""
    return get_mastery_list(student_id, subjectId)

@router.get("/insights/{student_id}")
def get_student_insights(student_id: str, subjectId: str, db: Connection = Depends(get_db)):
    """
    Returns structured analytics (JSON) for the Teacher Dashboard.
    If LLM generation is allowed by the active_profile, it could optionally invoke the LLM for summary.
    """
    analytics_json = generate_analytics(student_id, subjectId)
    
    # We could theoretically run LLM here if active_profile.enable_assessments or similar is true
    # But for deterministic stability we return the JSON. 
    return analytics_json

@router.get("/revision-plan/{student_id}")
def fetch_revision_plan(student_id: str, subjectId: str, db: Connection = Depends(get_db)):
    """Returns the deterministic study schedule."""
    return get_revision_plan(student_id, subjectId)

@router.post("/revision-plan/regenerate")
def regenerate_revision_plan(studentId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Triggers deterministic regeneration of the study schedule."""
    generate_revision_plan(studentId, subjectId)
    return {"status": "success", "message": "Revision plan regenerated"}
