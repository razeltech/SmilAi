import asyncio
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
import random
import uuid
import json
import logging
from datetime import datetime
from sqlite3 import Connection
from ..database.connection import get_db

from .schemas import ChatRequest
from ..rag.retrieve import staged_hybrid_search
from ..rag.inference import generate_rag_response_stream, prepare_search_query
from ..core.context import RequestContext
from ..core.dependencies import get_request_context

router = APIRouter(prefix="/chat", tags=["Chat & Inference"])



def is_smalltalk(msg: str) -> bool:
    cleaned = msg.strip().lower().replace("?", "").replace("!", "").replace(".", "").strip()
    
    # Common short greetings or conversational closures
    smalltalk_keywords = {
        "hello", "hi", "hey", "namaste", "good morning", "good afternoon", 
        "good evening", "how are you", "how r u", "how are you today",
        "who are you", "what is your name", "whats your name", "who r u",
        "bye", "goodbye", "thank you", "thanks", "ok", "okay", "yes", "no"
    }
    if cleaned in smalltalk_keywords:
        return True
        
    # Check for question words - if present, it's an academic query, not smalltalk
    question_words = {"what", "why", "how", "who", "when", "where", "which", "explain", "define", "solve", "tell"}
    words = set(cleaned.split())
    if words.intersection(question_words):
        return False
        
    # Heuristics for emotional chat and general check-ins
    emotional_keywords = {"tired", "sleepy", "bored", "exhausted", "sad", "happy", "excited", "scared", "fear", "worried", "stressed", "feeling"}
    academic_indicators = {"algebra", "equation", "solve", "math", "science", "history", "formula", "textbook", "lesson", "question", "chapter", "definition", "concept"}
    
    # If the message is short (<=2 words) or mentions emotional words, AND does not contain academic indicator words
    if (len(words) <= 2 or words.intersection(emotional_keywords)) and not words.intersection(academic_indicators):
        return True
        
    return False

async def chat_stream_generator(request: ChatRequest, client_request: Request):
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

        # Load history context from SQLite (last 6 messages)
        history = []
        if request.session_id and request.session_id != "new":
            def load_history_sync():
                conn = get_db_connection()
                try:
                    rows = conn.execute(
                        "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT 6",
                        (request.session_id,)
                    ).fetchall()
                    history_list = []
                    for row in reversed(rows):
                        history_list.append({
                            "role": "user" if row["role"] == "user" else "assistant",
                            "content": row["content"]
                        })
                    return history_list
                finally:
                    conn.close()
            history = await asyncio.to_thread(load_history_sync)

        # Check if the query is simple smalltalk
        smalltalk = is_smalltalk(request.message)

        retrieved_chunks = []
        filler = ""
        rewrite_data = {
            "query": request.message,
            "rewritten": False,
            "rewrite_skipped": True,
            "reason": "smalltalk_bypass" if smalltalk else ("empty_history_fallback" if not history else "no_change"),
            "rewrite_time_ms": 0
        }
        
        import time
        retrieval_time_ms = 0
        
        if not smalltalk:
            # Prepare search query (optional rewrite)
            rewrite_data = await prepare_search_query(request.message, history)
            search_query = rewrite_data["query"]
            
            # 2. Perform Staged Hybrid RAG Retrieval in a background thread with 5s timeout
            retrieval_start = time.perf_counter()
            try:
                retrieved_chunks = await asyncio.wait_for(
                    asyncio.to_thread(
                        staged_hybrid_search,
                        search_query,
                        "system_org", # In production, extract from JWT
                        request.subject_id,
                        5
                    ),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                retrieved_chunks = []
            retrieval_time_ms = int((time.perf_counter() - retrieval_start) * 1000)
        
        # 3. Stream the actual response directly from Ollama (Qwen 2.5)
        generation_start = time.perf_counter()
        assistant_response_only = ""
        disconnected = False
        llm_metrics = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "memory_count": 0}
        async for token in generate_rag_response_stream(
            request.message, 
            retrieved_chunks, 
            history=history, 
            is_conversational=smalltalk,
            student_id=request.user_id,
            subject_id=request.subject_id,
            metrics_out=llm_metrics
        ):
            if await client_request.is_disconnected():
                logger = logging.getLogger("uvicorn")
                logger.info("Client disconnected. Stream cancelled.")
                disconnected = True
                break
            assistant_response_only += token
            yield token
            
        if disconnected:
            return
            
        generation_time_ms = int((time.perf_counter() - generation_start) * 1000)

        # 4. Save assistant response in background thread (save only generated content, no filler)
        def save_assistant_response():
            conn = get_db_connection()
            try:
                ast_msg_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO chat_messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (ast_msg_id, session_id, "assistant", assistant_response_only, datetime.utcnow().isoformat())
                )
                conn.commit()
            finally:
                conn.close()
            
        await asyncio.to_thread(save_assistant_response)

        # Trigger Student Profile Memory Extraction asynchronously in the background
        try:
            from ..memory.service import extract_student_memory
            asyncio.create_task(
                extract_student_memory(
                    request.message,
                    assistant_response_only,
                    request.user_id,
                    request.subject_id
                )
            )
        except Exception as me:
            logger = logging.getLogger("uvicorn")
            logger.error(f"Failed to launch memory extraction task: {me}")

        # Gather metrics for telemetry
        top_similarity = 0.0
        if retrieved_chunks:
            first_chunk = retrieved_chunks[0]
            if isinstance(first_chunk, dict):
                top_similarity = first_chunk.get("score") or first_chunk.get("similarity") or 0.0
                
        metrics = {
            "session_id": session_id,
            "original_query": request.message,
            "prepared_query": rewrite_data["query"],
            "rewritten": rewrite_data["rewritten"],
            "rewrite_skipped": rewrite_data["rewrite_skipped"],
            "reason": rewrite_data["reason"],
            "rewrite_time_ms": rewrite_data["rewrite_time_ms"],
            "retrieval_time_ms": retrieval_time_ms,
            "generation_time_ms": generation_time_ms,
            "total_latency_ms": rewrite_data["rewrite_time_ms"] + retrieval_time_ms + generation_time_ms,
            "chunks_count": len(retrieved_chunks),
            "top_similarity": top_similarity,
            "llm_tokens": llm_metrics.get("total_tokens", 0),
            "prompt_tokens": llm_metrics.get("prompt_tokens", 0),
            "completion_tokens": llm_metrics.get("completion_tokens", 0),
            "context_size": 8192,
            "memory_count": llm_metrics.get("memory_count", 0),
            "rag_chunks_used": len(retrieved_chunks)
        }
        logger = logging.getLogger("uvicorn")
        logger.info(f"[METRIC] {json.dumps(metrics)}")
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w") as f:
            f.write(traceback.format_exc())
        raise

@router.post("/stream")
async def stream_chat(
    chat_request: ChatRequest, 
    request: Request, 
    db: Connection = Depends(get_db),
    context: RequestContext = Depends(get_request_context)
):
    """
    Primary RAG endpoint. Uses StreamingResponse to ensure the student never 
    sees a loading wheel, adhering to the 'Humanized Latency' design pattern.
    """
    from ..rag.guardrails import check_prompt
    from ..language.dependencies import get_language_adapter
    
    # 1. Guardrails Layer: fast offline check
    cleaned_message = check_prompt(chat_request.message)
    
    adapter = get_language_adapter()
    english_query = adapter.inbound(cleaned_message, context)
    chat_request.message = english_query
    
    return StreamingResponse(chat_stream_generator(chat_request, request), media_type="text/event-stream")

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

@router.delete("/sessions/{sessionId}")
def delete_session(sessionId: str, db: Connection = Depends(get_db)):
    """Deletes a chat session and all its messages."""
    try:
        db.execute("DELETE FROM chat_messages WHERE session_id = ?", (sessionId,))
        cursor = db.execute("DELETE FROM chat_sessions WHERE id = ?", (sessionId,))
        if cursor.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Session not found")
        db.commit()
        return {"message": "Success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
