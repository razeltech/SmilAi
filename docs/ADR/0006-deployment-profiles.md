# ADR-006: Deployment Profiles

## Decision
The platform will define capabilities dynamically based on Deployment Profiles:
- **Lite**: English only, Piper TTS, CPU inference.
- **Standard**: IndicTrans2 Distilled, Parler TTS, mid-tier GPU.
- **Pro**: IndicTrans2 Full, Parler TTS, high-tier GPU.

## Reason
Different educational institutions have vastly different hardware constraints. Features should gracefully degrade or disable rather than causing 500 internal server errors. Profiles ensure we know exactly what is supported in any given deployment.

## Status
Accepted
