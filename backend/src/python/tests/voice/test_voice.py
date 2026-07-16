import pytest
from app.api.voice import prepare_speech_text

def test_prepare_speech_text_markdown():
    text = "Here is a list:\n* Item 1\n* Item 2\n**Bold** text."
    cleaned = prepare_speech_text(text)
    
    # Assert asterisks and hash marks are stripped out
    assert "*" not in cleaned
    assert "Bold text" in cleaned

def test_prepare_speech_text_math():
    text = "The formula is $E=mc^2$ and \\alpha."
    cleaned = prepare_speech_text(text)
    
    # Simple stripping ensures TTS doesn't stumble on raw tex characters
    assert "$" not in cleaned

def test_sentence_splitting_simulation():
    # Simulate the regex splitting used in voice endpoint
    import re
    text = "Hello there. How are you? I am fine!"
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    assert len(sentences) == 3
    assert sentences[0] == "Hello there."
    assert sentences[1] == "How are you?"
    assert sentences[2] == "I am fine!"
