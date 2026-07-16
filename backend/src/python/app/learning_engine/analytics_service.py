import logging
from ..database.connection import get_db_connection
from .metrics import calculate_trend

logger = logging.getLogger(__name__)

def generate_analytics(student_id: str, subject_id: str) -> dict:
    """
    Computes deterministic JSON analytics for a student's performance.
    """
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT concept, mastery_score, confidence, evidence_count
            FROM concept_mastery
            WHERE student_id = ? AND subject_id = ?
            ORDER BY mastery_score DESC
            """, (student_id, subject_id)
        ).fetchall()
        
        if not rows:
            return {
                "strongest": [],
                "weakest": [],
                "average_mastery": 0.0,
                "trend": "Not enough data",
                "total_concepts": 0
            }
            
        concepts = [dict(r) for r in rows]
        total_mastery = sum(float(c["mastery_score"]) for c in concepts)
        average_mastery = total_mastery / len(concepts)
        
        # Sort for strongest/weakest
        sorted_by_mastery = sorted(concepts, key=lambda x: float(x["mastery_score"]))
        weakest = sorted_by_mastery[:3]
        strongest = sorted_by_mastery[-3:]
        
        # Fake a trend history since we don't have the history table yet
        # In the future, this will query the mastery_history table.
        # For now, we just pass the current average as a single point.
        trend = calculate_trend([average_mastery])
        
        return {
            "strongest": strongest,
            "weakest": weakest,
            "average_mastery": round(average_mastery, 2),
            "trend": trend,
            "total_concepts": len(concepts)
        }
    except Exception as e:
        logger.error(f"Failed to generate analytics: {e}")
        return {}
    finally:
        conn.close()

def get_mastery_list(student_id: str, subject_id: str) -> list:
    """
    Gets the raw mastery list for UI display (e.g., Progress Bars/Dots).
    """
    conn = get_db_connection()
    try:
        rows = conn.execute(
            """
            SELECT concept, mastery_score, confidence
            FROM concept_mastery
            WHERE student_id = ? AND subject_id = ?
            ORDER BY concept ASC
            """, (student_id, subject_id)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Failed to fetch mastery list: {e}")
        return []
    finally:
        conn.close()
