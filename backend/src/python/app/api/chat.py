import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import random
import uuid
from datetime import datetime
from sqlite3 import Connection
from ..database.connection import get_db

from .schemas import ChatRequest
from ..rag.retrieve import staged_hybrid_search
from ..rag.inference import generate_rag_response_stream

router = APIRouter(prefix="/chat", tags=["Chat & Inference"])

# Gentle, motherly filler phrases for 1st-10th graders to eliminate robot-latency.
FILLER_PHRASES = [
    "That's a wonderful question, my dear! Let me check the textbook...",
    "Give me just one moment to find the best answer for you...",
    "Hmm, let's think about that together... holding on just a second...",
    "I'm so glad you asked! Let me look that up really quickly..."
]

async def chat_stream_generator(request: ChatRequest):
    from ..database.connection import get_db_connection
    try:
        # Helper to run synchronous DB commits in background
        def save_session_and_message():
            # Open a dedicated connection for the background thread
            conn = get_db_connection()
            try:
                session_id = request.session_id
                if not session_id or session_id == "new":
                    session_id = str(uuid.uuid4())
                    title = request.message[:50] + ("..." if len(request.message) > 50 else "")
                    conn.execute(
                        "INSERT INTO chat_sessions (id, user_id, subject_id, title, created_at) VALUES (?, ?, ?, ?, ?)",
                        (session_id, request.user_id, request.subject_id, title, datetime.utcnow().isoformat())
                    )
                
                user_msg_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO chat_messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (user_msg_id, session_id, "user", request.message, datetime.utcnow().isoformat())
                )
                conn.commit()
                return session_id
            finally:
                conn.close()

        # Run DB insert in background
        session_id = await asyncio.to_thread(save_session_and_message)

        # 1. Instantly return a gentle filler phrase so the UI/TTS can start playing it
        filler = random.choice(FILLER_PHRASES)
        yield f"{filler}\n\n"
        
        # 2. Perform Staged Hybrid RAG Retrieval in a background thread
        retrieved_chunks = await asyncio.to_thread(
            staged_hybrid_search,
            request.message,
            "system_org", # In production, extract from JWT
            request.subject_id,
            5
        )
        
        # 3. Stream the actual response directly from Ollama (Qwen 2.5)
        full_response = filler + "\n\n"
        async for token in generate_rag_response_stream(request.message, retrieved_chunks):
            full_response += token
            yield token

        # 4. Save assistant response in background thread
        def save_assistant_response():
            conn = get_db_connection()
            try:
                ast_msg_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO chat_messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (ast_msg_id, session_id, "assistant", full_response, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()
            
        await asyncio.to_thread(save_assistant_response)
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        raise

@router.post("/stream")
async def stream_chat(request: ChatRequest, db: Connection = Depends(get_db)):
    """
    Primary RAG endpoint. Uses StreamingResponse to ensure the student never 
    sees a loading wheel, adhering to the 'Humanized Latency' design pattern.
    """
    return StreamingResponse(chat_stream_generator(request), media_type="text/event-stream")

@router.get("/sessions")
def get_sessions(userId: str, subjectId: str, db: Connection = Depends(get_db)):
    """Fetches all chat sessions for a student in a subject."""
    rows = db.execute(
        "SELECT * FROM chat_sessions WHERE user_id = ? AND subject_id = ? ORDER BY created_at DESC", 
        (userId, subjectId)
    ).fetchall()
    return [
        {
            "id": r["id"],
            "userId": r["user_id"],
            "subjectId": r["subject_id"],
            "title": r["title"],
            "createdAt": r["created_at"]
        }
        for r in rows
    ]

@router.get("/sessions/{sessionId}/messages")
def get_session_messages(sessionId: str, db: Connection = Depends(get_db)):
    """Fetches all messages for a specific chat session."""
    rows = db.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
        (sessionId,)
    ).fetchall()
    return [
        {
            "id": r["id"],
            "sessionId": r["session_id"],
            "role": r["role"],
            "content": r["content"],
            "timestamp": r["timestamp"],
            "citations": r.get("citations"),
            "audioUrl": r.get("audio_url")
        }
        for r in rows
    ]
