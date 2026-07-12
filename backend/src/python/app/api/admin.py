from fastapi import APIRouter, Depends
from sqlite3 import Connection

from ..database.connection import get_db

router = APIRouter(tags=["Admin & Data Routes"])

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

    # Map snake_case DB columns to camelCase for frontend
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

@router.get("/subjects/{subjectId}/assignments")
def get_subject_assignments(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all assignments for a subject."""
    rows = db.execute("SELECT * FROM assignments WHERE subject_id = ? ORDER BY due_date DESC", (subjectId,)).fetchall()
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

@router.get("/subjects/{subjectId}/assessments")
def get_subject_assessments(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all assessments for a subject."""
    rows = db.execute("SELECT * FROM assessments WHERE subject_id = ? ORDER BY created_at DESC", (subjectId,)).fetchall()
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

@router.get("/subjects/{subjectId}/documents")
def get_subject_documents(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all uploaded documents/syllabus for a subject."""
    rows = db.execute("SELECT * FROM documents WHERE subject_id = ? ORDER BY uploaded_at DESC", (subjectId,)).fetchall()
    return [
        {
            "id": r["id"],
            "subjectId": r["subject_id"],
            "orgId": r["org_id"],
            "name": r["name"],
            "type": r["type"],
            "chunkCount": r["chunk_count"],
            "uploadedAt": r["uploaded_at"]
        }
        for r in rows
    ]

@router.get("/subjects/{subjectId}/submissions")
def get_subject_submissions(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all code submissions for assignments in a subject."""
    rows = db.execute("""
        SELECT sub.*, a.title AS assignment_title 
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        WHERE a.subject_id = ?
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
    """Returns all assignments across all subjects."""
    rows = db.execute("SELECT * FROM assignments ORDER BY due_date DESC").fetchall()
    return [
        {
            "id": r["id"], "subjectId": r["subject_id"], "title": r["title"],
            "description": r["description"], "rubric": r["rubric"], "dueDate": r["due_date"]
        }
        for r in rows
    ]

@router.get("/assessments")
def get_assessments(db: Connection = Depends(get_db)):
    """Returns all assessments across all subjects."""
    rows = db.execute("SELECT * FROM assessments ORDER BY created_at DESC").fetchall()
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
    # Profile approvals table doesn't exist yet — return empty for now
    return []

@router.get("/students/{userId}/subjects/{subjectId}/record")
def get_student_record(userId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Aggregates a student's academic record for a specific subject."""
    # Get student name
    student = db.execute("SELECT name FROM users WHERE id = ?", (userId,)).fetchone()
    student_name = student["name"] if student else "Student"

    # Get subject name
    subject = db.execute("SELECT name FROM subjects WHERE id = ?", (subjectId,)).fetchone()
    subject_name = subject["name"] if subject else "Subject"

    # Aggregate assessment scores
    assessment_rows = db.execute("""
        SELECT a.name AS assessment_name, 
               SUM(sa.score) AS total_score,
               COUNT(sa.id) AS question_count,
               MAX(a.created_at) AS date
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN assessments a ON q.assessment_id = a.id
        WHERE sa.student_id = ? AND a.subject_id = ?
        GROUP BY a.id
        ORDER BY date DESC
    """, (userId, subjectId)).fetchall()

    # Aggregate code submission scores
    submission_rows = db.execute("""
        SELECT a.title, sub.score, sub.submitted_at AS date
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        WHERE sub.student_id = ? AND a.subject_id = ?
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
