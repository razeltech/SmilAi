import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

@pytest.fixture
def setup_db():
    from app.database.connection import get_db_connection
    conn = get_db_connection()
    org_id = f"org_{uuid.uuid4().hex[:8]}"
    teacher_id = f"teacher_{uuid.uuid4().hex[:8]}"
    subject_id = f"sub_{uuid.uuid4().hex[:8]}"
    
    conn.execute("INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)", (org_id, "Test Org"))
    conn.execute("INSERT OR IGNORE INTO users (id, name, email, password, role, org_id) VALUES (?, ?, ?, ?, ?, ?)",
                 (teacher_id, "Test Teacher", f"{teacher_id}@test.com", "pass", "teacher", org_id))
    conn.execute("INSERT OR IGNORE INTO grade_bands (id, org_id, name) VALUES (?, ?, ?)", ("grade_10", org_id, "Grade 10"))
    conn.execute("INSERT INTO subjects (id, org_id, grade_band_id, name, teacher_id) VALUES (?, ?, ?, ?, ?)",
                 (subject_id, org_id, "grade_10", "Test Subject", teacher_id))
    
    # Create Assessment
    assessment_id = f"ass_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT INTO assessments (id, subject_id, name, question_count, topic, difficulty, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (assessment_id, subject_id, "Test Assessment", 1, "Testing", "easy", "draft", "2024-01-01T00:00:00Z"))

    # Create Assignment
    assignment_id = f"assign_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT INTO assignments (id, subject_id, title, description, rubric, due_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (assignment_id, subject_id, "Test Assignment", "Desc", "Rubric", "2099-01-01", "draft"))

    # Create Question
    question_id = f"q_{uuid.uuid4().hex[:8]}"
    conn.execute("INSERT INTO questions (id, assessment_id, type, prompt, correct_answer) VALUES (?, ?, ?, ?, ?)",
                 (question_id, assessment_id, "short_answer", "What is 1+1?", "2"))
                 
    conn.commit()
    conn.close()
    yield {"subject_id": subject_id, "assessment_id": assessment_id, "assignment_id": assignment_id, "question_id": question_id}
    
    # Cleanup
    # conn = get_db_connection()
    # conn.execute("PRAGMA foreign_keys = OFF;")
    # conn.execute("DELETE FROM questions WHERE assessment_id = ?", (assessment_id,))
    # conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    # conn.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
    # conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    # conn.commit()
    # conn.close()

def test_patch_assessment(setup_db):
    assessment_id = setup_db["assessment_id"]
    payload = {"status": "published"}
    res = client.patch(f"/v1/assessments/{assessment_id}", json=payload)
    assert res.status_code == 200
    assert res.json()["message"] == "Success"

def test_patch_assignment(setup_db):
    assignment_id = setup_db["assignment_id"]
    payload = {"status": "published"}
    res = client.patch(f"/v1/assignments/{assignment_id}", json=payload)
    assert res.status_code == 200
    assert res.json()["message"] == "Success"

def test_patch_question(setup_db):
    question_id = setup_db["question_id"]
    payload = {"prompt": "What is 2+2?", "correct_answer": "4"}
    res = client.patch(f"/v1/questions/{question_id}", json=payload)
    assert res.status_code == 200
    assert res.json()["message"] == "Success"
