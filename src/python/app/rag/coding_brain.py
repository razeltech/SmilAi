import httpx
import ast
import json
from fastapi import APIRouter, HTTPException

from .inference import OLLAMA_URL, LLM_MODEL

router = APIRouter(prefix="/coding", tags=["Coding Brain"])

CODING_BRAIN_PROMPT = """You are Smiley, the coding mentor for this student.
The student has submitted code that is broken or contains a logic error.
Your job is to act like a gentle, patient older sibling.
DO NOT GIVE THE DIRECT ANSWER OR THE FULL CORRECTED CODE.
Instead, guide them to figure it out themselves. Ask a guiding question or point out the line where the logic goes wrong.
Use simple, friendly language."""

def basic_static_analysis(code_string: str):
    """
    Ensures the code doesn't contain glaring syntax errors before sending to the LLM.
    We NEVER use exec() or eval() for security reasons.
    """
    try:
        ast.parse(code_string)
        return True, "Syntax is valid. Checking logic..."
    except SyntaxError as e:
        return False, f"Oops! There seems to be a syntax error on line {e.lineno}: {e.msg}"

@router.post("/analyze")
async def analyze_student_code(student_code: str, assignment_rubric: str):
    """
    Endpoint used by the Student Dashboard when they submit code.
    Provides immediate, gentle feedback using Qwen-2.5 local logic.
    """
    is_valid, syntax_msg = basic_static_analysis(student_code)
    
    if not is_valid:
        # Return immediate syntax help without bothering the LLM
        return {"feedback": syntax_msg, "status": "syntax_error"}

    prompt = f"""
    Assignment Rubric / Goal:
    {assignment_rubric}
    
    Student's Submitted Code:
    ```python
    {student_code}
    ```
    
    Please provide gentle, guiding feedback.
    """

    payload = {
        "model": LLM_MODEL,
        "system": CODING_BRAIN_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.4 # Slightly lower for strict coding logic
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload, timeout=60.0)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="LLM Engine Error")
            
            data = response.json()
            return {"feedback": data.get("response", ""), "status": "logic_review"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
