from datetime import datetime, timedelta

def compute_next_review(mastery: float, review_count: int) -> str:
    """
    Simple spaced repetition interval calculation.
    Returns ISO datetime string for next review.
    """
    # Base interval in hours
    if mastery < 0.4:
        interval_hours = 24
    elif mastery < 0.7:
        interval_hours = 72
    else:
        interval_hours = 168 # 1 week
        
    # Multiplier based on successful review count
    multiplier = 1.5 ** review_count
    
    final_hours = min(interval_hours * multiplier, 720) # Max 1 month
    dt = datetime.utcnow() + timedelta(hours=final_hours)
    return dt.isoformat()
