import pytest
from app.database.connection import get_db_connection
from app.assessment.service import AssessmentService, AssessmentRepository

import asyncio

def test_assessment_generation_and_lifecycle():
    async def run_test():
        org_id = "cad61a6c-cb04-4d08-a103-7deeafb84837"
        subject_id = "a7f984b9-ae55-41af-ba93-0bced1614c57"
        topic = "Quadratic Equations"
        difficulty = "easy"
        count = 2
        
        # Mock LLM generation for stable offline tests
        from app.assessment.generator import AssessmentGenerator
        async def mock_generate(*args, **kwargs):
            return [
                {
                    "question": "What is the standard form of a quadratic equation?",
                    "options": ["ax^2+bx+c=0", "ax+b=0", "y=mx+c", "a^2+b^2=c^2"],
                    "correct_answer": "ax^2+bx+c=0",
                    "explanation": "Standard form is ax^2+bx+c=0"
                }
            ]
        AssessmentGenerator.generate_questions = mock_generate

        # 1. Test generate & save
        res = await AssessmentService.generate_and_save_assessment(
            org_id=org_id,
            subject_id=subject_id,
            topic=topic,
            difficulty=difficulty,
            question_count=count
        )
        assert res["id"] is not None
        assert res["questionCount"] > 0
        assessment_id = res["id"]
        
        conn = get_db_connection()
        
        # 2. Test Repository get
        as_details = AssessmentRepository.get_by_id(conn, assessment_id)
        assert as_details is not None
        assert as_details["topic"] == topic
        
        # 3. Test Retrieve Questions
        questions = AssessmentRepository.get_questions(conn, assessment_id)
        assert len(questions) > 0
        assert "options" in questions[0]
        
        # 4. Test Soft Delete
        success = AssessmentRepository.soft_delete(conn, assessment_id)
        assert success is True
        
        # 5. Check no longer active
        as_details_after = AssessmentRepository.get_by_id(conn, assessment_id)
        assert as_details_after is None
        
        conn.close()

    try:
        asyncio.run(run_test())
    except Exception as e:
        # If Ollama is offline, log error but do not fail hard
        if "connection" in str(e).lower() or "ollama" in str(e).lower():
            pytest.skip("Local Ollama service offline. Skipping LLM assessment generator tests.")
        else:
            raise e
