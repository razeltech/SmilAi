# ADR-004: Translation Adapter Pattern

## Decision
Implement Regional Language support (v1.4) via a "Translate-RAG-Translate" wrapper around the core English pipeline, rather than embedding translation awareness deep inside internal subsystems.

## Reason
Embedding language detection and localized prompt building directly into RAG, Memory, and Learning modules would pollute their isolated responsibilities and bloat testing requirements exponentially. Keeping the core strictly English-only isolates complexity.

## Benefits
* No schema changes required for local databases.
* No prompt engineering changes required for extraction or guardrails.
* No modifications needed to the deterministic learning engine.
* Safe, predictable rollouts: if translation fails, it can gracefully fall back to English without crashing the internal pipeline.

## Status
Accepted
