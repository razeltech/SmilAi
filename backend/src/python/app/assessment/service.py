import uuid
import json
import logging
from datetime import datetime
from sqlite3 import Connection

from ..database.connection import get_db_connection
from ..rag.retrieve import staged_hybrid_search
from .generator import AssessmentGenerator

logger = logging.getLogger(__name__)

class AssessmentRepository:
    @staticmethod
    def list_active(db: Connection, subject_id: str) -> list[dict]:
        """Returns all active (non-deleted) assessments for a subject."""
        rows = db.execute(
            "SELECT * FROM assessments WHERE subject_id = ? AND deleted_at IS NULL ORDER BY created_at DESC",
            (subject_id,)
        ).fetchall()
        return rows

    @staticmethod
    def get_by_id(db: Connection, assessment_id: str) -> dict:
        """Retrieves assessment details by ID."""
        row = db.execute("SELECT * FROM assessments WHERE id = ? AND deleted_at IS NULL", (assessment_id,)).fetchone()
        return row

    @staticmethod
    def get_questions(db: Connection, assessment_id: str) -> list[dict]:
        """Retrieves all questions associated with an assessment."""
        rows = db.execute(
            "SELECT * FROM questions WHERE assessment_id = ?",
            (assessment_id,)
        ).fetchall()
        # Parse choices JSON back into array for frontend
        results = []
        for r in rows:
            dict_row = dict(r)
            try:
                parsed_choices = json.loads(dict_row.get("choices", "[]"))
            except Exception:
                parsed_choices = []
            dict_row["choices"] = parsed_choices
            dict_row["options"] = parsed_choices
            results.append(dict_row)
        return results

    @staticmethod
    def soft_delete(db: Connection, assessment_id: str) -> bool:
        """Soft deletes an assessment by updating deleted_at column."""
        now_str = datetime.utcnow().isoformat()
        cursor = db.execute(
            "UPDATE assessments SET deleted_at = ? WHERE id = ?",
            (now_str, assessment_id)
        )
        db.commit()
        return cursor.rowcount > 0

class AssessmentService:
    @staticmethod
    async def generate_and_save_assessment(
        org_id: str,
        subject_id: str,
        topic: str,
        difficulty: str,
        question_count: int
    ) -> dict:
        """
        Coordinates context retrieval, generation from local Qwen model,
        and transactionally saves assessment metadata + questions to SQLite.
        """
        # 1. Retrieve curriculum context chunks
        try:
            retrieved_chunks = staged_hybrid_search(
                query=topic,
                org_id=org_id,
                subject_id=subject_id,
                top_k=10
            )
        except Exception as re:
            logger.warning(f"RAG search error during assessment generation (falling back to model knowledge): {re}")
            retrieved_chunks = []
            
        if retrieved_chunks:
            context_text = "\n\n".join([chunk['text'] for chunk in retrieved_chunks])
        else:
            context_text = f"(No custom textbook syllabus context available in vector store. Generate standard questions for topic: {topic}.)"

        # 2. Call generator to prompt local Ollama model
        questions = await AssessmentGenerator.generate_questions(
            context_text=context_text,
            topic=topic,
            difficulty=difficulty,
            count=question_count
        )

        if not questions:
            raise ValueError("LLM generated empty quiz array")

        # 3. Transactionally save to SQLite
        assessment_id = str(uuid.uuid4())
        name = f"{topic} Quiz ({difficulty.capitalize()})"
        created_at = datetime.utcnow().isoformat()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        
        try:
            # Insert assessment metadata
            cursor.execute(
                "INSERT INTO assessments (id, subject_id, name, question_count, topic, difficulty, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (assessment_id, subject_id, name, len(questions), topic, difficulty, created_at)
            )
            
            # Insert each generated question
            for q in questions:
                question_id = str(uuid.uuid4())
                options_str = json.dumps(q.get("options", q.get("choices", [])))
                cursor.execute(
                    "INSERT INTO questions (id, assessment_id, type, prompt, choices, correct_answer, source_citations) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        question_id,
                        assessment_id,
                        "mcq",
                        q.get("question", q.get("prompt", "")),
                        options_str,
                        q.get("correct_answer", ""),
                        q.get("explanation", "")
                    )
                )
                
            conn.commit()
            return {
                "id": assessment_id,
                "name": name,
                "questionCount": len(questions),
                "topic": topic,
                "difficulty": difficulty,
                "createdAt": created_at,
                "questions": questions
            }
            
        except Exception as e:
            cursor.execute("ROLLBACK;")
            logger.error(f"Transaction failed. Rolled back assessment creation: {e}")
            raise e
        finally:
            conn.close()
