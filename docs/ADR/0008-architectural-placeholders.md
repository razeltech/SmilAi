# ADR-008: Architectural Placeholders

## Decision
Never remove architectural placeholders (interfaces, abstract classes, or stub modules) without explicit approval from a lead architect. A stub throwing a `NotImplementedError` is considered valid architecture, representing future platform evolution, not dead code.

## Reason
SmilAI is an evolving platform. Deleting interfaces prematurely destroys the scaffolding required for future capability sprints. While implementations may be deferred, the structural boundaries they represent must remain intact unless the core architecture itself changes.

## Status
Accepted
