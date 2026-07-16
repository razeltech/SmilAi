from sqlite3 import Connection
from typing import Dict, Any, List

def get_org_settings(db: Connection) -> Dict[str, Any]:
    org = db.execute("SELECT * FROM organizations LIMIT 1").fetchone()
    if org:
        return {
            "name": org.get("name", "SmilAI Academy"),
            "boardType": org.get("board_type", "ap_govt_ssc"),
            "schoolCode": org.get("school_code", ""),
            "theme": "dark"
        }
    return {"name": "SmilAI Academy", "boardType": "ap_govt_ssc", "theme": "dark"}

def get_all_users(db: Connection) -> List[Dict[str, Any]]:
    rows = db.execute("SELECT id, name, email, role, org_id FROM users").fetchall()
    return [
        {"id": r["id"], "name": r["name"], "email": r["email"], "role": r["role"], "orgId": r["org_id"]}
        for r in rows
    ]

def get_user_profile(db: Connection, user_id: str) -> Dict[str, Any]:
    user = db.execute("SELECT id, name, email, role, org_id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return None
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

def get_student_record(db: Connection, user_id: str, subject_id: str) -> Dict[str, Any]:
    student = db.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()
    student_name = student["name"] if student else "Student"

    subject = db.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
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
    """, (user_id, subject_id)).fetchall()

    submission_rows = db.execute("""
        SELECT a.title, sub.score, sub.submitted_at AS date
        FROM submissions sub
        JOIN assignments a ON sub.assignment_id = a.id
        WHERE sub.student_id = ? AND a.subject_id = ? AND a.deleted_at IS NULL
        ORDER BY sub.submitted_at DESC
    """, (user_id, subject_id)).fetchall()

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
        "studentId": user_id,
        "studentName": student_name,
        "subjectId": subject_id,
        "subjectName": subject_name,
        "assessmentsCompleted": len(recent_assessments),
        "averageScore": avg_score,
        "submissionsCompleted": len(recent_submissions),
        "recentAssessments": recent_assessments[:5],
        "recentSubmissions": recent_submissions[:5]
    }
