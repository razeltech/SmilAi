from fastapi import APIRouter

router = APIRouter(tags=["Legacy Admin Mocks"])

@router.get("/org-settings")
def get_org_settings():
    return {
        "name": "SmilAI Global Academy",
        "theme": "dark"
    }

@router.get("/subjects")
def get_subjects(userId: str = None, role: str = None):
    # Return a mock mathematical subject to get Sharma (the student) booted in
    return [
        {
            "id": "math_101",
            "name": "Advanced Mathematics",
            "gradeBandId": "grade_10",
            "teacherId": "system_teacher"
        }
    ]

@router.get("/subjects/{subjectId}/assignments")
def get_subject_assignments(subjectId: str):
    return []

@router.get("/subjects/{subjectId}/assessments")
def get_subject_assessments(subjectId: str):
    return []

@router.get("/subjects/{subjectId}/documents")
def get_subject_documents(subjectId: str):
    return []

@router.get("/subjects/{subjectId}/submissions")
def get_subject_submissions(subjectId: str):
    return []

@router.get("/grade-bands")
def get_grade_bands():
    return []

@router.get("/users")
def get_users():
    return []

@router.get("/assignments")
def get_assignments():
    return []

@router.get("/assessments")
def get_assessments():
    return []

@router.get("/teacher/{userId}/pending-approval")
def get_pending_approvals(userId: str):
    return []

@router.get("/students/{userId}/subjects/{subjectId}/record")
def get_student_record(userId: str, subjectId: str):
    return {"grade": "A", "progress": 100}
