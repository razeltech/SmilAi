import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import random

from .schemas import ChatRequest

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
    
    # 2. [Future Phase 2] Simulate heavy RAG ingestion & Ollama inference delay
    # Here we will later call: 
    # context = retrieve_from_chromadb(...)
    # response_stream = query_ollama_qwen(...)
    await asyncio.sleep(2.5) # Simulating Vector Search + LLM Bootup
    
    # 3. Stream the actual response (Mocked for Phase 1)
    mock_answer = (
        "Alright, I found it! According to Chapter 4 in your Science book, "
        "the Earth revolves around the sun because of gravity. "
        "It acts like an invisible string pulling them together! Does that make sense?"
    )
    
    # Stream word by word to feel natural and gentle
    for word in mock_answer.split(" "):
        yield f"{word} "
        await asyncio.sleep(0.05) # Simulate token generation speed

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Primary RAG endpoint. Uses StreamingResponse to ensure the student never 
    sees a loading wheel, adhering to the 'Humanized Latency' design pattern.
    """
    return StreamingResponse(chat_stream_generator(request), media_type="text/event-stream")
