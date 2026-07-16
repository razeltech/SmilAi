# SmilAI Engineering Rules

These rules govern all AI-assisted development and architectural decisions on the SmilAI platform. They must be strictly adhered to by all contributors and automated agents.

1. **Preserve Architectural Placeholders**: Never delete placeholder interfaces, abstract classes, or stub modules unless explicitly instructed by the lead architect. A stub throwing `NotImplementedError` is considered valid architecture, not dead code.
2. **Advice != Permission**: Architectural advice or discussion is not implementation permission. Wait for explicit approval before altering the architecture.
3. **Preserve Public Interfaces**: Maintain the stability of public interfaces (like Providers and Contexts) whenever possible to prevent cascading breakages.
4. **One Concern Per Commit**: Refactor one subsystem per commit. Never combine Dependency Injection, file deletion, service refactors, router refactors, and provider changes into a single monolithic commit.
5. **Approval Threshold**: If a proposed architectural change affects more than 5 files, stop and request explicit approval before modifying code.
6. **Deprecate, Don't Delete**: Prefer deprecating old modules over outright deleting them until the migration is fully verified.
7. **ADR Governance**: All major decisions must be codified as an Architecture Decision Record (ADR) in the `docs/ADR/` directory. Future proposals must be validated against existing ADRs.
