from datetime import datetime
import logging
from ..database.connection import get_db_connection
from .metrics import calculate_mastery, calculate_confidence
from .scheduler import compute_next_review
from ..core.config.base import LEARNING_WEIGHTS

logger = logging.getLogger(__name__)

def update_mastery(student_id: str, subject_id: str, concept: str, score: float, event_type: str):
    """
    Updates the concept_mastery table based on a new evidence event.
    """
    # 1. Look up weight based on event_type
    weight = LEARNING_WEIGHTS.get(event_type, 0.2)
    
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT * FROM concept_mastery WHERE student_id = ? AND subject_id = ? AND concept = ?",
            (student_id, subject_id, concept)
        ).fetchone()
        
        now_str = datetime.utcnow().isoformat()
        
        if row:
            current_mastery = float(row["mastery_score"])
            current_conf = float(row["confidence"])
            evidence_count = int(row["evidence_count"]) + 1
            review_count = int(row["review_count"])
            
            # Compute new metrics
            new_mastery = calculate_mastery(current_mastery, weight, score)
            new_conf = calculate_confidence(current_conf, evidence_count, weight)
            
            correct = int(row["correct_answers"])
            incorrect = int(row["incorrect_answers"])
            
            # Simple threshold for correct/incorrect tracking
            if score >= 0.7:
                correct += 1
            elif score <= 0.3:
                incorrect += 1
                
            last_mastered_at = row["last_mastered_at"]
            if new_mastery >= 0.8:
                last_mastered_at = now_str
                
            # If they just answered something right, that counts as a successful review
            if score >= 0.7 and event_type in ("assessment", "practice"):
                review_count += 1
                
            next_review_at = compute_next_review(new_mastery, review_count)
            
            conn.execute("""
                UPDATE concept_mastery 
                SET mastery_score = ?, confidence = ?, evidence_count = ?, correct_answers = ?, 
                    incorrect_answers = ?, last_seen_at = ?, last_mastered_at = ?, 
                    review_count = ?, next_review_at = ?, updated_at = ?
                WHERE student_id = ? AND subject_id = ? AND concept = ?
            """, (new_mastery, new_conf, evidence_count, correct, incorrect, now_str, 
                  last_mastered_at, review_count, next_review_at, now_str, 
                  student_id, subject_id, concept))
        else:
            # First time seeing this concept
            new_mastery = calculate_mastery(0.0, weight, score) # Starts at 0, bumps up depending on score and weight
            new_conf = calculate_confidence(0.0, 1, weight)
            
            correct = 1 if score >= 0.7 else 0
            incorrect = 1 if score <= 0.3 else 0
            last_mastered_at = now_str if new_mastery >= 0.8 else None
            review_count = 1 if score >= 0.7 else 0
            next_review_at = compute_next_review(new_mastery, review_count)
            
            conn.execute("""
                INSERT INTO concept_mastery (
                    student_id, subject_id, concept, mastery_score, confidence, evidence_count, 
                    correct_answers, incorrect_answers, last_seen_at, last_mastered_at, 
                    review_count, next_review_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, subject_id, concept, new_mastery, new_conf, 1, 
                  correct, incorrect, now_str, last_mastered_at, 
                  review_count, next_review_at, now_str))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to update mastery for {concept}: {e}")
    finally:
        conn.close()
