from fastapi import APIRouter, HTTPException, Depends
import httpx
import json

from .schemas import ChatRequest
from ..database.connection import get_db
from ..rag.retrieve import staged_hybrid_search
from ..rag.inference import OLLAMA_URL, LLM_MODEL

router = APIRouter(prefix="/assessments", tags=["Assessment Brain"])

ASSESSMENT_PROMPT = """You are Smiley, an expert curriculum designer.
Based on the provided textbook context, generate a 3-question multiple-choice quiz.
Return the quiz STRICTLY as a JSON array of objects.
Each object must have: 'question', 'options' (array of 4 strings), 'correct_answer', and 'explanation'.
Do not include markdown blocks, just the raw JSON array."""

@router.post("/generate")
async def generate_assessment(topic: str, org_id: str, subject_id: str):
    """
    Teacher Dashboard endpoint.
    Retrieves semantic chunks for the requested topic, and asks the local LLM
    to generate an assessment specifically based on that school's curriculum.
    """
    # 1. Retrieve the relevant textbook chapters
    retrieved_chunks = staged_hybrid_search(
        query=topic,
        org_id=org_id,
        subject_id=subject_id,
        top_k=10
    )

    if not retrieved_chunks:
        raise HTTPException(status_code=404, detail="No syllabus data found for this topic.")

    context_text = "\n\n".join([chunk['text'] for chunk in retrieved_chunks])

    prompt = f"Context:\n{context_text}\n\nTopic: {topic}\n\nPlease generate the JSON quiz."

    payload = {
        "model": LLM_MODEL,
        "system": ASSESSMENT_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json", # Force JSON mode in Ollama
        "options": {
            "temperature": 0.2
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OLLAMA_URL, json=payload, timeout=120.0)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="LLM Generation Error")
            
            data = response.json()
            quiz_json = json.loads(data.get("response", "[]"))
            return {"topic": topic, "quiz": quiz_json}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
