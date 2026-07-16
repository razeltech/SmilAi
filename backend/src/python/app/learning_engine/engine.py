import logging
from .mastery_service import update_mastery
from .revision_service import generate_revision_plan

logger = logging.getLogger(__name__)

class LearningEngine:
    """
    Central entry point for all learning-related events.
    Decides whether to route to mastery updates, revision scheduling, or analytics.
    """
    
    @staticmethod
    def record_event(student_id: str, subject_id: str, event_type: str, payload: dict):
        """
        Record a learning event and trigger downstream updates.
        
        event_types:
        - 'assessment_completed': payload={"concept": str, "score": float}
        - 'question_answered': payload={"concept": str, "score": float}
        - 'chat_interaction': payload={"concept": str, "score": float}
        - 'teacher_override': payload={"concept": str, "score": float}
        - 'revision_completed': payload={"concept": str, "score": float}
        """
        try:
            concept = payload.get("concept")
            score = payload.get("score")
            
            if concept is None or score is None:
                logger.warning(f"Invalid payload for learning event '{event_type}': {payload}")
                return
                
            concept = concept.lower().strip()
            
            # 1. Update Mastery deterministically
            update_mastery(student_id, subject_id, concept, float(score), event_type)
            
            # 2. Trigger Revision Plan Re-generation
            # We don't want to do this on every single chat interaction, maybe just assessments.
            # But since it's deterministic and fast (SQLite), we can do it safely.
            if event_type in ("assessment_completed", "revision_completed", "teacher_override"):
                generate_revision_plan(student_id, subject_id)
                
            logger.info(f"LearningEngine recorded '{event_type}' for student {student_id}, concept '{concept}'")
        except Exception as e:
            logger.error(f"Error in LearningEngine.record_event: {e}")
