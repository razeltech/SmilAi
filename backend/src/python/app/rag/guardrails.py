import re
from fastapi import HTTPException

# 1. Size Validation constants
MAX_INPUT_LENGTH = 1000  # Restrict huge copy-pastes

# 2. Prompt Injection basic signatures
# This is a basic offline heuristic approach. 
PROMPT_INJECTION_SIGNATURES = [
    r"ignore (all )?previous instructions",
    r"forget (all )?previous instructions",
    r"you are now (chatgpt|claude|gemini|a different ai)",
    r"reveal (your )?(hidden )?prompt",
    r"bypass (the )?system",
    r"system prompt",
]
INJECTION_REGEX = re.compile("|".join(PROMPT_INJECTION_SIGNATURES), re.IGNORECASE)

# 3. Profanity basic list (Placeholder for a more robust offline classifier)
PROFANITY_WORDS = {"fuck", "shit", "bitch", "asshole"}

def validate_input_size(text: str):
    if len(text) > MAX_INPUT_LENGTH:
        raise HTTPException(status_code=400, detail="Input is too long. Please ask a shorter question.")

def validate_encoding(text: str):
    try:
        # Ensure it's valid UTF-8 and strip any weird invisible characters if needed
        text.encode('utf-8').decode('utf-8')
    except UnicodeError:
        raise HTTPException(status_code=400, detail="Invalid character encoding detected.")

def detect_prompt_injection(text: str):
    if INJECTION_REGEX.search(text):
        raise HTTPException(status_code=400, detail="Security policy violation: Prompt injection attempt detected.")

def check_profanity(text: str):
    words = set(re.findall(r'\b\w+\b', text.lower()))
    for p in PROFANITY_WORDS:
        if any(p in w for w in words):
            raise HTTPException(status_code=400, detail="Security policy violation: Inappropriate language detected.")

def check_unsafe_requests(text: str):
    # E.g. violent content, self-harm keywords
    unsafe_keywords = {"kill", "suicide", "murder", "bomb", "weapon"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words.intersection(unsafe_keywords):
        raise HTTPException(status_code=400, detail="Security policy violation: Unsafe request detected.")

def check_prompt(user_input: str) -> str:
    """
    Executes the sequential guardrails pipeline.
    Throws HTTPException if any layer fails, preventing expensive LLM compute.
    Returns cleaned unicode string.
    """
    if not user_input or not user_input.strip():
        raise HTTPException(status_code=400, detail="Input cannot be empty.")
        
    cleaned = user_input.strip()
    
    validate_input_size(cleaned)
    validate_encoding(cleaned)
    detect_prompt_injection(cleaned)
    check_profanity(cleaned)
    check_unsafe_requests(cleaned)
    
    return cleaned
