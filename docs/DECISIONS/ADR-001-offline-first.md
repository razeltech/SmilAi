# ADR-001: Offline-First Architecture

## Decision
Design the entire SmilAI platform to run completely offline without any cloud dependencies (no OpenAI, no Gemini, no AWS).

## Reason
SmilAI is targeted at educational environments (like rural schools or budget constrained environments) that cannot guarantee stable internet access or pay recurring token costs for LLM APIs.

## Benefits
* Absolute data privacy (COPPA compliant by default).
* Zero recurring operational costs for API usage.
* Predictable latency depending purely on local hardware.
* Highly resilient; network outages do not disrupt the learning experience.

## Status
Accepted
