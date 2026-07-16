from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...database.connection import get_db
from ...assessment.service import AssessmentRepository, AssessmentService

router = APIRouter(tags=["Admin - Assessments"])

class AssessmentPostRequest(BaseModel):
    topic: str
    difficulty: str
    questionCount: int

class AssessmentPatchRequest(BaseModel):
    status: Optional[str] = None

class QuestionPatchRequest(BaseModel):
    prompt: Optional[str] = None
    choices: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[str] = None

@router.get("/assessments")
def get_all_assessments(db: Connection = Depends(get_db)):
    """Returns all active assessments across all subjects."""
    rows = db.execute("SELECT * FROM assessments WHERE deleted_at IS NULL ORDER BY created_at DESC").fetchall()
    return [
        {
            "id": r["id"], "subjectId": r["subject_id"], "name": r["name"],
            "questionCount": r["question_count"], "topic": r["topic"],
            "difficulty": r["difficulty"], "createdAt": r["created_at"]
        }
        for r in rows
    ]

@router.get("/subjects/{subjectId}/assessments")
def get_subject_assessments(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all active assessments for a subject."""
    rows = AssessmentRepository.list_active(db, subjectId)
    return [
        {
            "id": r["id"],
            "subjectId": r["subject_id"],
            "name": r["name"],
            "questionCount": r["question_count"],
            "topic": r["topic"],
            "difficulty": r["difficulty"],
            "createdAt": r["created_at"]
        }
        for r in rows
    ]

@router.post("/subjects/{subjectId}/assessments")
async def generate_subject_assessment(subjectId: str, req: AssessmentPostRequest, db: Connection = Depends(get_db)):
    """Triggers LLM generation of a multiple choice quiz and saves to database."""
    subject = db.execute("SELECT org_id FROM subjects WHERE id = ?", (subjectId,)).fetchone()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    org_id = subject["org_id"]
    
    try:
        res = await AssessmentService.generate_and_save_assessment(
            org_id=org_id,
            subject_id=subjectId,
            topic=req.topic,
            difficulty=req.difficulty,
            question_count=req.questionCount
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment generation failed: {str(e)}")

@router.get("/assessments/{id}")
def get_assessment_details(id: str, db: Connection = Depends(get_db)):
    """Returns assessment details along with its questions."""
    assessment = AssessmentRepository.get_by_id(db, id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    questions = AssessmentRepository.get_questions(db, id)
    return {
        "id": assessment["id"],
        "subjectId": assessment["subject_id"],
        "name": assessment["name"],
        "questionCount": assessment["question_count"],
        "topic": assessment["topic"],
        "difficulty": assessment["difficulty"],
        "createdAt": assessment["created_at"],
        "questions": questions
    }

@router.patch("/assessments/{id}")
def edit_assessment(id: str, req: AssessmentPatchRequest, db: Connection = Depends(get_db)):
    """Updates assessment status."""
    updates = []
    params = []
    if req.status is not None:
        updates.append("status = ?")
        params.append(req.status)
        if req.status == "published":
            updates.append("published_at = ?")
            params.append(datetime.utcnow().isoformat())
            
    if not updates:
        return {"message": "Success"}
        
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(id)
    
    query = f"UPDATE assessments SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL"
    db.execute(query, tuple(params))
    db.commit()
    return {"message": "Success"}

@router.patch("/questions/{id}")
def edit_question(id: str, req: QuestionPatchRequest, db: Connection = Depends(get_db)):
    """Updates a question inside an assessment."""
    updates = []
    params = []
    if req.prompt is not None:
        updates.append("prompt = ?")
        params.append(req.prompt)
    if req.choices is not None:
        updates.append("choices = ?")
        params.append(req.choices)
    if req.correct_answer is not None:
        updates.append("correct_answer = ?")
        params.append(req.correct_answer)
    if req.explanation is not None:
        updates.append("explanation = ?")
        params.append(req.explanation)
    if req.difficulty is not None:
        updates.append("difficulty = ?")
        params.append(req.difficulty)
        
    if not updates:
        return {"message": "Success"}
        
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(id)
    
    query = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"
    db.execute(query, tuple(params))
    db.commit()
    return {"message": "Success"}

@router.delete("/assessments/{id}")
def remove_assessment(id: str, db: Connection = Depends(get_db)):
    """Soft deletes an assessment."""
    db.execute(
        "UPDATE assessments SET deleted_at = ? WHERE id = ?",
        (datetime.utcnow().isoformat(), id)
    )
    db.commit()
    return {"message": "Success"}
