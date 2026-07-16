import math
from datetime import datetime, timedelta

def calculate_mastery(current_mastery: float, evidence_weight: float, score: float) -> float:
    """
    Exponential moving average to update mastery.
    """
    # Dampen the evidence weight based on how much it diverges from current
    return current_mastery * (1.0 - evidence_weight) + (score * evidence_weight)

def calculate_confidence(current_conf: float, evidence_count: int, new_evidence_weight: float) -> float:
    """
    Confidence increases logarithmically with evidence count, up to 1.0.
    """
    # Simple logarithmic curve peaking around 20 pieces of evidence
    base_conf = min(0.95, math.log10(evidence_count + 1) / math.log10(20))
    # Mix with the current explicit confidence
    return max(base_conf, current_conf + (1.0 - current_conf) * 0.1)

def calculate_priority(mastery: float, confidence: float, next_review_at: str) -> int:
    """
    Calculate a priority score from 1-100 for revision planning.
    Higher priority for lower mastery, lower confidence, and overdue dates.
    """
    score = 100
    
    # Mastery Penalty (up to 40 points)
    score -= (mastery * 40)
    
    # Confidence Penalty (up to 20 points)
    score -= (confidence * 20)
    
    # Overdue Bonus (up to 40 points)
    if next_review_at:
        try:
            dt = datetime.fromisoformat(next_review_at)
            days_overdue = (datetime.utcnow() - dt).total_seconds() / 86400
            if days_overdue > 0:
                score += min(40, int(days_overdue * 5))
            else:
                score -= 10 # Not due yet
        except Exception:
            pass
            
    return max(1, min(100, int(score)))

def calculate_trend(mastery_history: list) -> str:
    """
    Determine trend based on a list of historical mastery scores (oldest to newest).
    """
    if len(mastery_history) < 2:
        return "Not enough data"
        
    first = mastery_history[0]
    last = mastery_history[-1]
    
    diff = last - first
    if diff > 0.1:
        return "Improving"
    elif diff < -0.1:
        return "Declining"
    return "Stable"


