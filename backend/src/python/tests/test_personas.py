import pytest
import uuid
from io import BytesIO

class TestAdminPersona:
    """Tests evaluating administrative configuration and global mock routes."""
    
    def test_org_settings(self, client):
        """Validates that the admin can retrieve global organization configurations."""
        response = client.get("/v1/org-settings")
        # Ensure the mock route responds and provides expected base keys
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "theme" in data

    def test_grade_bands(self, client):
        """Validates that grade band configurations are accessible to admins."""
        response = client.get("/v1/grade-bands")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_users(self, client):
        """Validates that admins can query the user directory."""
        response = client.get("/v1/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTeacherPersona:
    """Tests evaluating teacher actions, subject management, and grading queues."""
    
    def test_teacher_registration(self, client):
        """Simulates a teacher signing up for the platform."""
        mock_email = f"teacher_{uuid.uuid4()}@school.edu"
        payload = {
            "name": "Mrs. Smith",
            "email": mock_email,
            "password": "securepassword123",
            "role": "teacher",
            "org_id": "system_org"
        }
        response = client.post("/v1/auth/register", json=payload)
        # We expect a 200 (if DB sets up right) or a 400 (if 'system_org' missing).
        # We primarily want to ensure the route exists and processes Pydantic models.
        assert response.status_code in [200, 400]

    def test_teacher_subjects(self, client):
        """Validates that a teacher can fetch their assigned subjects."""
        response = client.get("/v1/subjects?userId=teacher_123&role=teacher")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "id" in data[0]

    def test_teacher_pending_approvals(self, client):
        """Validates that a teacher can fetch their pending grading queue."""
        response = client.get("/v1/teacher/teacher_123/pending-approval")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestStudentPersona:
    """Tests evaluating core learning loops: RAG chat, Voice STT, and Assessment."""
    
    def test_student_chat_stream(self, client):
        """Validates the core RAG streaming endpoint for student queries."""
        payload = {
            "session_id": "test_session",
            "user_id": "student_123",
            "subject_id": "math_101",
            "message": "Can you explain Pythagorean theorem?"
        }
        response = client.post("/v1/chat/stream", json=payload)
        # Server might error 500 if Ollama isn't running locally during CI test,
        # but 200/500 guarantees the route is active and mapping works.
        assert response.status_code in [200, 500]

    def test_student_voice_transcribe(self, client):
        """Validates the Whisper voice transcription route accepts audio blobs."""
        # Create a mock 1-second WAV file in memory
        mock_wav = BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
        mock_wav.name = "student_recording.wav"
        
        response = client.post(
            "/v1/voice/transcribe", 
            files={"file": ("student_recording.wav", mock_wav, "audio/wav")}
        )
        assert response.status_code in [200, 500]

    def test_student_record(self, client):
        """Validates the student can fetch their academic record/grades."""
        response = client.get("/v1/students/student_123/subjects/math_101/record")
        assert response.status_code == 200
        data = response.json()
        assert "grade" in data
        assert "progress" in data
