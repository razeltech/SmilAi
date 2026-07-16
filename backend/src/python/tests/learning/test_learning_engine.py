import pytest
from app.learning_engine.metrics import calculate_mastery, calculate_confidence, calculate_priority, calculate_trend

def test_metrics_mastery():
    # From 0, heavy weight (assessment=0.6) and perfect score (1.0)
    m1 = calculate_mastery(0.0, 0.6, 1.0)
    assert m1 == 0.6
    
    # From 0.6, small weight (chat=0.2) and perfect score (1.0)
    m2 = calculate_mastery(0.6, 0.2, 1.0)
    assert round(m2, 2) == 0.68
    
    # From 0.8, heavy weight (assessment=0.6) and fail score (0.0)
    m3 = calculate_mastery(0.8, 0.6, 0.0)
    assert round(m3, 2) == 0.32

def test_learning_weights_config():
    from app.core.config.base import LEARNING_WEIGHTS
    assert LEARNING_WEIGHTS["assessment"] == 0.6
    assert LEARNING_WEIGHTS["chat"] == 0.2
    assert LEARNING_WEIGHTS["teacher"] == 1.0

def test_metrics_confidence():
    c1 = calculate_confidence(0.0, 1, 0.6)
    assert c1 > 0.0
    c2 = calculate_confidence(c1, 10, 0.2)
    assert c2 > c1

def test_metrics_priority():
    # Low mastery, low conf, due date passed = high priority
    p1 = calculate_priority(0.2, 0.2, "2020-01-01T00:00:00")
    assert p1 > 80
    
    # High mastery, high conf, due date future = low priority
    p2 = calculate_priority(0.9, 0.9, "2050-01-01T00:00:00")
    assert p2 < 50

def test_metrics_trend():
    assert calculate_trend([0.2, 0.3, 0.4]) == "Improving"
    assert calculate_trend([0.8, 0.7, 0.5]) == "Declining"
    assert calculate_trend([0.5, 0.55]) == "Stable"
