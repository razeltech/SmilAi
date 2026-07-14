from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

from ..database.connection import get_db
from ..documents.service import DocumentRepository, DocumentService
from ..assessment.service import AssessmentRepository, AssessmentService

router = APIRouter(tags=["Admin & Data Routes"])

# Pydantic Request Schemas
class BulkDocItem(BaseModel):
    name: str
    content: str
    parserType: str = "auto"
    type: str = "library"

class BulkDocRequest(BaseModel):
    documents: list[BulkDocItem]

class DocumentPatch(BaseModel):
    status: str

class AssessmentPostRequest(BaseModel):
    topic: str
    difficulty: str
    questionCount: int

class AssignmentPostRequest(BaseModel):
    subjectId: str
    title: str
    description: str
    rubric: str
    dueDate: str

class OverrideGradeRequest(BaseModel):
    score: int
    feedback: str

# GET Endpoints
@router.get("/org-settings")
def get_org_settings(db: Connection = Depends(get_db)):
    """Returns the first organization's settings."""
    org = db.execute("SELECT * FROM organizations LIMIT 1").fetchone()
    if org:
        return {
            "name": org.get("name", "SmilAI Academy"),
            "boardType": org.get("board_type", "ap_govt_ssc"),
            "schoolCode": org.get("school_code", ""),
            "theme": "dark"
        }
    return {"name": "SmilAI Academy", "boardType": "ap_govt_ssc", "theme": "dark"}

@router.get("/subjects")
def get_subjects(userId: str = None, role: str = None, db: Connection = Depends(get_db)):
    """Returns subjects based on user role - enrolled subjects for students, owned for teachers, all for admin."""
    if role == "admin" or not userId:
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
        """).fetchall()
    elif role == "teacher":
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE s.teacher_id = ?
        """, (userId,)).fetchall()
    else:
        # Student — return enrolled subjects
        subjects = db.execute("""
            SELECT s.id, s.org_id, s.grade_band_id, s.name, s.teacher_id,
                   gb.name AS grade_band_name, u.name AS teacher_name
            FROM subjects s
            JOIN enrollments e ON e.subject_id = s.id
            LEFT JOIN grade_bands gb ON s.grade_band_id = gb.id
            LEFT JOIN users u ON s.teacher_id = u.id
            WHERE e.user_id = ?
        """, (userId,)).fetchall()

    return [
        {
            "id": s["id"],
            "orgId": s["org_id"],
            "gradeBandId": s["grade_band_id"],
            "name": s["name"],
            "teacherId": s["teacher_id"],
            "gradeBandName": s.get("grade_band_name", ""),
            "teacherName": s.get("teacher_name", "")
        }
        for s in subjects
    ]

# CRUD - Documents
@router.get("/subjects/{subjectId}/documents")
def get_subject_documents(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all active uploaded documents for a subject."""
    rows = DocumentRepository.list_active(db, subjectId)
    return [
        {
            "id": r["id"],
            "subjectId": r["subject_id"],
            "orgId": r["org_id"],
            "name": r["name"],
            "type": r["type"],
            "chunkCount": r["chunk_count"],
            "uploadedAt": r["uploaded_at"],
            "status": r.get("status", "approved")
        }
        for r in rows
    ]

@router.post("/subjects/{subjectId}/documents/bulk")
def upload_subject_documents_bulk(subjectId: str, req: BulkDocRequest, db: Connection = Depends(get_db)):
    """Transactionally ingests multiple documents for a subject."""
    subject = db.execute("SELECT org_id FROM subjects WHERE id = ?", (subjectId,)).fetchone()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    org_id = subject["org_id"]
    
    docs_processed = []
    total_chunks = 0
    for doc in req.documents:
        try:
            res = DocumentService.ingest_parsed_document(
                filename=doc.name,
                content=doc.content,
                org_id=org_id,
                subject_id=subjectId
            )
            total_chunks += res["total_chunks"]
            docs_processed.append({
                "id": res["doc_id"],
                "name": doc.name,
                "status": "pending"
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to ingest doc '{doc.name}': {str(e)}")
            
    return {
        "processedCount": len(docs_processed),
        "totalChunks": total_chunks,
        "documents": docs_processed
    }

@router.patch("/documents/{id}")
def patch_document(id: str, req: DocumentPatch, db: Connection = Depends(get_db)):
    """Updates a document's status (approved, archived, pending)."""
    success = DocumentRepository.patch_status(db, id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success", "status": req.status}

@router.post("/documents/{id}/approve")
def approve_document(id: str, db: Connection = Depends(get_db)):
    """Convenience endpoint specifically called by frontend to approve document."""
    success = DocumentRepository.patch_status(db, id, "approved")
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success", "status": "approved"}

@router.delete("/documents/{id}")
def delete_document(id: str, db: Connection = Depends(get_db)):
    """Soft deletes a document by setting status = 'archived'."""
    success = DocumentRepository.soft_delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success"}

# CRUD - Assessments
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

@router.delete("/assessments/{id}")
def delete_assessment(id: str, db: Connection = Depends(get_db)):
    """Soft deletes an assessment."""
    success = AssessmentRepository.soft_delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"message": "Success"}

# CRUD - Assignments
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

# Other general routes
@router.get("/grade-bands")
def get_grade_bands(db: Connection = Depends(get_db)):
    """Returns all grade bands."""
    rows = db.execute("SELECT * FROM grade_bands").fetchall()
    return [{"id": r["id"], "orgId": r["org_id"], "name": r["name"]} for r in rows]

@router.get("/users")
def get_users(db: Connection = Depends(get_db)):
    """Returns all users (admin only, no passwords)."""
    rows = db.execute("SELECT id, name, email, role, org_id FROM users").fetchall()
    return [
        {"id": r["id"], "name": r["name"], "email": r["email"], "role": r["role"], "orgId": r["org_id"]}
        for r in rows
    ]

@router.get("/users/{user_id}/profile")
def get_user_profile(user_id: str, db: Connection = Depends(get_db)):
    """Fetches profile data for a user."""
    user = db.execute("SELECT id, name, email, role, org_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return {"error": "User not found"}
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "orgId": user["org_id"],
        "phone": "",
        "bio": "",
        "grade": "",
        "board": ""
    }

@router.get("/assignments")
def get_assignments(db: Connection = Depends(get_db)):
    """Returns all active assignments across all subjects."""
    rows = db.execute("SELECT * FROM assignments WHERE deleted_at IS NULL ORDER BY due_date DESC").fetchall()
    return [
        {
            "id": r["id"], "subjectId": r["subject_id"], "title": r["title"],
            "description": r["description"], "rubric": r["rubric"], "dueDate": r["due_date"]
        }
        for r in rows
    ]

@router.get("/assessments")
def get_assessments(db: Connection = Depends(get_db)):
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

@router.get("/teacher/{userId}/pending-approval")
def get_pending_approvals(userId: str, db: Connection = Depends(get_db)):
    """Returns pending profile approvals for a teacher."""
    return []

@router.get("/students/{userId}/subjects/{subjectId}/record")
def get_student_record(userId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Aggregates a student's academic record for a specific subject."""
    student = db.execute("SELECT name FROM users WHERE id = ?", (userId,)).fetchone()
    student_name = student["name"] if student else "Student"

    subject = db.execute("SELECT name FROM subjects WHERE id = ?", (subjectId,)).fetchone()
    subject_name = subject["name"] if subject else "Subject"

    assessment_rows = db.execute("""
        SELECT a.name AS assessment_name, 
               SUM(sa.score) AS total_score,
               COUNT(sa.id) AS question_count,
               MAX(a.created_at) AS date
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN assessments a ON q.assessment_id = a.id
        WHERE sa.student_id = ? AND a.subject_id = ? AND a.deleted_at IS NULL
        GROUP BY a.id
        ORDER BY date DESC
    """, (userId, subjectId)).fetchall()

    submission_rows = db.execute("""
        SELECT a.title, sub.score, sub.submitted_at AS date
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        WHERE sub.student_id = ? AND a.subject_id = ? AND a.deleted_at IS NULL
        ORDER BY sub.submitted_at DESC
    """, (userId, subjectId)).fetchall()

    recent_assessments = [
        {
            "assessmentName": r["assessment_name"],
            "score": r["total_score"] or 0,
            "total": r["question_count"] * 10,
            "date": r["date"] or ""
        }
        for r in assessment_rows
    ]

    recent_submissions = [
        {
            "title": r["title"],
            "score": r["score"] or 0,
            "date": r["date"] or ""
        }
        for r in submission_rows
    ]

    avg_score = 0
    if recent_assessments:
        total_earned = sum(a["score"] for a in recent_assessments)
        total_possible = sum(a["total"] for a in recent_assessments)
        avg_score = round((total_earned / total_possible * 100), 1) if total_possible > 0 else 0

    return {
        "studentId": userId,
        "studentName": student_name,
        "subjectId": subjectId,
        "subjectName": subject_name,
        "assessmentsCompleted": len(recent_assessments),
        "averageScore": avg_score,
        "submissionsCompleted": len(recent_submissions),
        "recentAssessments": recent_assessments[:5],
        "recentSubmissions": recent_submissions[:5]
    }
