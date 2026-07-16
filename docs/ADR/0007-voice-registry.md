# ADR-007: Voice Registry and Persona Mapping

## Decision
Voice engine selection (e.g., determining which `.onnx` file or `voice_id` to use) is strictly separated from the Voice Engine itself. A `VoiceRegistry` inside the Language Layer decides the `voice_id` based on `(locale, persona, gender, deployment_profile)`.

## Reason
The TTS Engine should only be responsible for converting text to audio using a specified voice model. It shouldn't know about user preferences or languages. By isolating this logic, we can trivially add new personas (like "Storyteller", "Child") or new languages without altering the TTS core.

## Status
Accepted
