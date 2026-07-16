import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid
import sqlite3

client = TestClient(app)

@pytest.fixture
def setup_db():
    from app.database.connection import get_db_connection
    conn = get_db_connection()
    # Create an org and a teacher to satisfy FK constraints if needed
    org_id = f"org_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)", (org_id, "Test Org"))
    
    teacher_id = f"teacher_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT OR IGNORE INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)",
                 (teacher_id, "Test Teacher", f"{teacher_id}@test.com", "pass", "teacher", org_id))
    
    conn.commit()
    conn.close()
    
    yield {"org_id": org_id, "teacher_id": teacher_id}
    
    # Cleanup (optional if using a persistent dev db, but good practice for testing)
    # conn = get_db_connection()
    # conn.execute("PRAGMA foreign_keys = OFF;")
    # conn.execute("DELETE FROM subjects WHERE org_id = ?", (org_id,))
    # conn.execute("DELETE FROM grade_bands WHERE org_id = ?", (org_id,))
    # conn.execute("DELETE FROM users WHERE org_id = ?", (org_id,))
    # conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
    # conn.commit()
    # conn.close()

def test_admin_subjects_crud(setup_db):
    org_id = setup_db["org_id"]
    teacher_id = setup_db["teacher_id"]
    
    # Create Subject
    payload = {
        "orgId": org_id,
        "name": "Test Physics",
        "teacherId": teacher_id,
        "gradeBandId": "grade_10",
        "category": "SCIENCE",
        "supportsProjects": 0,
        "isActive": 1
    }
    create_res = client.post("/v1/subjects", json=payload)
    assert create_res.status_code == 200
    subject_id = create_res.json().get("id") or create_res.json().get("subject_id")
    assert subject_id is not None

    # Get Subjects
    get_res = client.get(f"/v1/subjects?org_id={org_id}")
    assert get_res.status_code == 200
    subjects = get_res.json()
    assert any(s["id"] == subject_id for s in subjects)

    # Patch Subject
    patch_payload = {
        "supportsProjects": 1,
        "isActive": 0
    }
    patch_res = client.patch(f"/v1/subjects/{subject_id}", json=patch_payload)
    assert patch_res.status_code == 200
    
    # Verify Patch
    get_res2 = client.get(f"/v1/subjects?org_id={org_id}")
    patched_subject = next(s for s in get_res2.json() if s["id"] == subject_id)
    # the response uses camelCase
    assert patched_subject.get("supportsProjects", patched_subject.get("supports_projects")) == 1
    assert patched_subject.get("isActive", patched_subject.get("is_active")) == 0

    # Delete Subject
    del_res = client.delete(f"/v1/subjects/{subject_id}")
    assert del_res.status_code == 200
    
def test_admin_enroll_student(setup_db):
    from app.database.connection import get_db_connection
    conn = get_db_connection()
    org_id = setup_db["org_id"]
    teacher_id = setup_db["teacher_id"]
    
    # Create Student
    student_id = f"student_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT OR IGNORE INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)",
                 (student_id, "Test Student", f"{student_id}@test.com", "pass", "student", org_id))
    
    # Create Subject
    subject_id = f"sub_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT OR IGNORE INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)", ("grade_10", org_id, "Grade 10"))
    conn.execute("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)",
                 (subject_id, org_id, "grade_10", "Enroll Test", teacher_id))
    conn.commit()
    conn.close()

    enroll_payload = {
        "userId": student_id
    }
    enroll_res = client.post(f"/v1/subjects/{subject_id}/enroll", json=enroll_payload)
    assert enroll_res.status_code == 200
    
    # Duplicate enrollment should return 200 (if handled gracefully) or 400
    enroll_res_dup = client.post(f"/v1/subjects/{subject_id}/enroll", json=enroll_payload)
    assert enroll_res_dup.status_code in [200, 400]
