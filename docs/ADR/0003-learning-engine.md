# ADR-003: Deterministic Learning Engine

## Decision
All mastery updates, revision scheduling, priority calculation, and analytics within the Learning Engine must be deterministic Python algorithms rather than LLM-driven reasoning.

## Reason
LLMs are probabilistic and prone to hallucination. Using an LLM to "grade" a student's overall mastery or "plan" their revision schedule leads to inconsistent educational outcomes and makes debugging pedagogical issues impossible. 

## Benefits
* 100% predictable, testable, and reproducible grading scales.
* Fast execution (Python math is sub-millisecond, whereas LLM reasoning takes seconds).
* Allows teachers to explicitly weight inputs (e.g. Assessments = 0.6, Chat = 0.2).
* Guarantees compliance with strict curriculum standards.

## Status
Accepted
