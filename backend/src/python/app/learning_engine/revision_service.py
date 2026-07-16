import uuid
from datetime import datetime
import logging
from ..database.connection import get_db_connection
from .metrics import calculate_priority

logger = logging.getLogger(__name__)

def generate_revision_plan(student_id: str, subject_id: str):
    """
    Deterministically generates or updates a revision plan based on current mastery and scheduled review dates.
    """
    conn = get_db_connection()
    try:
        # Get all concepts for the student that are due for review or have low mastery
        now_str = datetime.utcnow().isoformat()
        rows = conn.execute(
            """
            SELECT concept, mastery_score, confidence, next_review_at
            FROM concept_mastery
            WHERE student_id = ? AND subject_id = ?
            """, (student_id, subject_id)
        ).fetchall()
        
        for r in rows:
            concept = r["concept"]
            mastery = float(r["mastery_score"])
            conf = float(r["confidence"])
            next_review = r["next_review_at"]
            
            priority = calculate_priority(mastery, conf, next_review)
            
            # If priority is reasonably high, ensure it's in the revision plan
            if priority >= 30:
                # Check if an active plan exists
                existing = conn.execute(
                    """
                    SELECT id FROM revision_plans 
                    WHERE student_id = ? AND subject_id = ? AND concept = ? AND status = 'pending'
                    """, (student_id, subject_id, concept)
                ).fetchone()
                
                if existing:
                    # Update priority if it changed
                    conn.execute(
                        "UPDATE revision_plans SET priority_score = ? WHERE id = ?",
                        (priority, existing["id"])
                    )
                else:
                    # Create new plan
                    plan_id = str(uuid.uuid4())
                    scheduled_date = next_review if next_review else now_str
                    conn.execute(
                        """
                        INSERT INTO revision_plans (
                            id, student_id, subject_id, concept, priority_score, 
                            scheduled_date, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                        """, (plan_id, student_id, subject_id, concept, priority, scheduled_date, now_str)
                    )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to generate revision plan: {e}")
    finally:
        conn.close()

def get_revision_plan(student_id: str, subject_id: str) -> list:
    """
    Retrieves the prioritized revision plan for a student.
    """
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, concept, priority_score, scheduled_date
            FROM revision_plans
            WHERE student_id = ? AND subject_id = ? AND status = 'pending'
            ORDER BY priority_score DESC, scheduled_date ASC
            """, (student_id, subject_id)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to fetch revision plan: {e}")
        return []
    finally:
        conn.close()
