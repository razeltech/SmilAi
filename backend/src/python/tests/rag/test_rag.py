import pytest
from app.rag.prompt_builder import PROMPT_BUILDER

def test_prompt_builder_history_injection():
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    messages = PROMPT_BUILDER.build(
        query="What is algebra?",
        retrieved_chunks=[],
        history=history,
        is_conversational=False,
        profile_card=""
    )
    
    # Expected: persona + 2 history + user query = 4 messages
    assert len(messages) == 4
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello"

def test_prompt_builder_memory_injection():
    messages = PROMPT_BUILDER.build(
        query="What is algebra?",
        retrieved_chunks=[],
        history=[],
        profile_card="Student struggles with fractions."
    )
    
    # Expected: persona + memory + query = 3 messages
    assert len(messages) == 3
    assert messages[1]["role"] == "system"
    assert "fractions" in messages[1]["content"]

def test_prompt_builder_chunk_formatting():
    chunks = [
        {"text": "Algebra is math.", "source": "math.pdf"},
        {"text": "It uses variables.", "source": "math.pdf"}
    ]
    messages = PROMPT_BUILDER.build(
        query="What is algebra?",
        retrieved_chunks=chunks,
        is_conversational=False
    )
    
    user_message = messages[-1]["content"]
    assert "Passage [1] (Source: math.pdf)" in user_message
    assert "Algebra is math." in user_message
    assert "Passage [2]" in user_message
