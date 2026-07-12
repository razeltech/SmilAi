import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import random
from sqlite3 import Connection
from ..database.connection import get_db

from .schemas import ChatRequest
from ..rag.retrieve import staged_hybrid_search
from ..rag.inference import generate_rag_response_stream

router = APIRouter(prefix="/chat", tags=["Chat & Inference"])

# Gentle, motherly filler phrases for 1st-10th graders to eliminate robot-latency.
FILLER_PHRASES = [
    "Hmm, let me think about that for a second...",
    "That's a wonderful question! Let me look that up for you...",
    "Give me just one moment to find the best answer...",
    "I'm checking your textbook right now, hold on just a second..."
]

async def chat_stream_generator(request: ChatRequest):
    """
    Generates a streaming response that immediately engages the student,
    hiding the latency of the local Vector DB and LLM RAG process.
    """
    # 1. Instantly return a gentle filler phrase so the UI/TTS can start playing it
    filler = random.choice(FILLER_PHRASES)
    yield f"{filler}\n\n"
    
    # 2. Perform Staged Hybrid RAG Retrieval
    # (SQL Metadata Pre-Filter -> ChromaDB Vector -> Cross-Encoder)
    retrieved_chunks = staged_hybrid_search(
        query=request.message,
        org_id="system_org", # In production, extract from JWT
        subject_id=request.subject_id,
        top_k=5
    )
    
    # 3. Stream the actual response directly from Ollama (Qwen 2.5)
    async for token in generate_rag_response_stream(request.message, retrieved_chunks):
        yield token

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Primary RAG endpoint. Uses StreamingResponse to ensure the student never 
    sees a loading wheel, adhering to the 'Humanized Latency' design pattern.
    """
    return StreamingResponse(chat_stream_generator(request), media_type="text/event-stream")

@router.get("/sessions")
def get_sessions(userId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Fetches all chat sessions for a student in a subject."""
    sessions = db.execute(
        "SELECT * FROM chat_sessions WHERE user_id = ? AND subject_id = ? ORDER BY created_at DESC", 
        (userId, subjectId)
    ).fetchall()
    return sessions
