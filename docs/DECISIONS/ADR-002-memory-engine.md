# ADR-002: Modular Memory Engine

## Decision
Separate the Memory Engine into two distinct phases: SQLite+Chroma for Retrieval, and Ollama for Extraction. Establish a strict confidence threshold (e.g., > 0.70) for committing new profile traits.

## Reason
If a local LLM handles both chat generation and memory extraction simultaneously, the context window gets bloated and hallucinations can corrupt the student's long-term profile. Memory extraction needs to happen asynchronously.

## Benefits
* Fast, lightweight chat streaming since memory extraction is offloaded to the background.
* High fidelity profile traits. Low-confidence hallucinations are automatically rejected by the threshold.
* Clear boundaries: Retrieval uses traditional DB tools (Chroma/SQLite), keeping the LLM scoped to extraction reasoning only.

## Status
Accepted
