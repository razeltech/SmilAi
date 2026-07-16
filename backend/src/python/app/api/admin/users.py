from fastapi import APIRouter, Depends
from sqlite3 import Connection
from ...database.connection import get_db
from ...user.service import get_org_settings, get_all_users, get_user_profile, get_student_record

router = APIRouter(tags=["Admin - Users"])

@router.get("/org-settings")
def org_settings(db: Connection = Depends(get_db)):
    """Returns the first organization's settings."""
    return get_org_settings(db)

@router.get("/users")
def get_users_list(db: Connection = Depends(get_db)):
    """Returns all users (admin only, no passwords)."""
    return get_all_users(db)

@router.get("/users/{user_id}/profile")
def user_profile(user_id: str, db: Connection = Depends(get_db)):
    """Fetches profile data for a user."""
    profile = get_user_profile(db, user_id)
    if not profile:
        return {"error": "User not found"}
    return profile

@router.get("/teacher/{userId}/pending-approval")
def pending_approvals(userId: str, db: Connection = Depends(get_db)):
    """Returns pending profile approvals for a teacher."""
    return []

@router.get("/students/{userId}/subjects/{subjectId}/record")
def student_record(userId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Aggregates a student's academic record for a specific subject."""
    return get_student_record(db, userId, subjectId)
