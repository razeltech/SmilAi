# ADR-005: Provider Abstraction Pattern

## Decision
All AI interactions (Inference, Language Translation, Voice Synthesis, Embeddings, Caching) must inherit from a unified `BaseProvider` interface with consistent `initialize()`, `health()`, and `capabilities()` signatures.

## Reason
Hardcoding logic for specific models (like Ollama, IndicTrans2, or Piper) deeply into the application logic makes swapping them impossible without widespread refactoring. SmilAI must remain engine-agnostic to support rapid adoption of newer, smaller models without architecture drift.

## Status
Accepted
