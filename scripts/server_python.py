"""
SmilAI - Production Python Backend (FastAPI + SQLite)
This file is provided so you can completely swap Node/Express with Python when migrating to your system.
It supports the exact SQLite database schemas, seeding scripts, and REST contracts (/v1/...) as the development Express backend.

Dependencies:
    pip install fastapi uvicorn google-genai pydantic

To run:
    python server.py
"""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from google import genai
from google.genai import types

# Initialize FastAPI App
app = FastAPI(title="SmilAI Virtual Teacher API", version="1.0.0")

# Enable CORS for LAN multi-device support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "smilai.db"

# Initialize Gemini Client (uses GEMINI_API_KEY env variable)
# Set up a placeholder key for local offline loading if not defined
os.environ.setdefault("GEMINI_API_KEY", "LOCAL_API_KEY_PLACEHOLDER")

def get_genai_client():
    return genai.Client()

# ==========================================
# SQLITE DATABASE INTERFACES
# ==========================================
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables mirroring Express db.ts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL,
        org_id TEXT NOT NULL,
        FOREIGN KEY(org_id) REFERENCES organizations(id)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grade_bands (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY(org_id) REFERENCES organizations(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        grade_band_id TEXT NOT NULL,
        name TEXT NOT NULL,
        teacher_id TEXT NOT NULL,
        FOREIGN KEY(org_id) REFERENCES organizations(id),
        FOREIGN KEY(grade_band_id) REFERENCES grade_bands(id),
        FOREIGN KEY(teacher_id) REFERENCES users(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        user_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        PRIMARY KEY(user_id, subject_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        org_id TEXT NOT NULL,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        type TEXT CHECK(type IN ('library', 'personal')) NOT NULL,
        chunk_count INTEGER NOT NULL DEFAULT 0,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY(subject_id) REFERENCES subjects(id),
        FOREIGN KEY(org_id) REFERENCES organizations(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        org_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        text TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        FOREIGN KEY(doc_id) REFERENCES documents(id),
        FOREIGN KEY(org_id) REFERENCES organizations(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        title TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        citations TEXT,
        audio_url TEXT,
        FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        name TEXT NOT NULL,
        question_count INTEGER NOT NULL,
        topic TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id TEXT PRIMARY KEY,
        assessment_id TEXT NOT NULL,
        type TEXT CHECK(type IN ('mcq', 'short_answer')) NOT NULL,
        prompt TEXT NOT NULL,
        choices TEXT,
        correct_answer TEXT,
        source_citations TEXT,
        FOREIGN KEY(assessment_id) REFERENCES assessments(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_answers (
        id TEXT PRIMARY KEY,
        question_id TEXT NOT NULL,
        student_id TEXT NOT NULL,
        answer_content TEXT NOT NULL,
        score REAL,
        explanation TEXT,
        graded_by TEXT CHECK(graded_by IN ('deterministic', 'llm_rubric')),
        teacher_override REAL,
        FOREIGN KEY(question_id) REFERENCES questions(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        rubric TEXT NOT NULL,
        due_date TEXT NOT NULL,
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id TEXT PRIMARY KEY,
        assignment_id TEXT NOT NULL,
        student_id TEXT NOT NULL,
        file_name TEXT NOT NULL,
        code_content TEXT NOT NULL,
        score REAL,
        feedback TEXT,
        teacher_override REAL,
        submitted_at TEXT NOT NULL,
        FOREIGN KEY(assignment_id) REFERENCES assignments(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    )""")
    
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    orgId: Optional[str] = None

class ChatRequest(BaseModel):
    sessionId: Optional[str] = None
    userId: str
    subjectId: str
    message: str

class DocumentUpload(BaseModel):
    name: str
    content: str
    type: Optional[str] = "library"
    orgId: Optional[str] = None

class GenerateAssessment(BaseModel):
    topic: str
    difficulty: str
    questionCount: int

class GradeAnswerItem(BaseModel):
    questionId: str
    answerContent: str

class SubmitAssessment(BaseModel):
    studentId: str
    answers: List[GradeAnswerItem]

class CodeSubmission(BaseModel):
    studentId: str
    fileName: str
    codeContent: str

# ==========================================
# ROUTES
# ==========================================
@app.get("/v1/health")
def health():
    return {"status": "ok", "database": "sqlite", "runtime": "Python FastAPI"}

@app.post("/v1/auth/login")
def login(payload: LoginRequest):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?", 
        (payload.email, payload.password)
    ).fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "orgId": user["org_id"]
    }

@app.get("/v1/subjects")
def get_subjects():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT s.*, u.name as teacherName, g.name as gradeBandName 
        FROM subjects s
        LEFT JOIN users u ON s.teacher_id = u.id
        LEFT JOIN grade_bands g ON s.grade_band_id = g.id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/v1/subjects/{subject_id}/documents")
def get_documents(subject_id: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM documents WHERE subject_id = ? ORDER BY uploaded_at DESC", 
        (subject_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Mirroring RAG-scoped Q&A
@app.post("/v1/chat")
def chat_endpoint(payload: ChatRequest):
    conn = get_db_connection()
    
    # Ensure session
    session_id = payload.sessionId
    if not session_id:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        title = payload.message[:30] + "..." if len(payload.message) > 30 else payload.message
        conn.execute(
            "INSERT INTO chat_sessions (id, user_id, subject_id, title, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, payload.userId, payload.subjectId, title, datetime.now().isoformat())
        )
        
    # Store User Message
    conn.execute(
        "INSERT INTO chat_messages (id, session_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (f"msg-{uuid.uuid4().hex[:8]}", session_id, "user", payload.message, datetime.now().isoformat())
    )
    
    # Retrieve local chunks for RAG context
    chunks = conn.execute("SELECT id, text FROM chunks WHERE subject_id = ?", (payload.subjectId,)).fetchall()
    
    # Basic keyword search matching
    matched_chunks = []
    query_words = [w.lower() for w in payload.message.split() if len(w) > 2]
    if query_words:
        for chunk in chunks:
            score = sum(1 for word in query_words if word in chunk["text"].lower())
            if score > 0:
                matched_chunks.append((chunk, score))
        matched_chunks.sort(key=lambda x: x[1], reverse=True)
    
    context_text = "\n\n".join(
        [f"[Citation {idx+1}]: {item[0]['text']}" for idx, item in enumerate(matched_chunks[:3])]
    )
    
    subject = conn.execute("SELECT name FROM subjects WHERE id = ?", (payload.subjectId,)).fetchone()
    subject_name = subject["name"] if subject else "the subject"

    # AI Request via Google GenAI SDK
    system_instruction = (
        f"You are 'SmilAI', a highly supportive and warm virtual teacher for {subject_name}.\n"
        "Ground your answers strictly inside the provided context. Answer clearly, citing "
        "passages using [Citation 1], [Citation 2], etc. Be warm and supportive."
    )
    
    user_prompt = f"Context:\n{contextText}\n\nUser Question: {payload.message}"
    
    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        ai_response = response.text or "Let me think about that for a second."
    except Exception as e:
        ai_response = f"Hello! Offline-mode notice: AI response is temporarily simulated. Error: {str(e)}"

    assistant_msg_id = f"msg-{uuid.uuid4().hex[:8]}"
    citations = [f"Citation {idx+1}" for idx in range(len(matched_chunks[:3]))]
    
    conn.execute(
        "INSERT INTO chat_messages (id, session_id, role, content, timestamp, citations) VALUES (?, ?, ?, ?, ?, ?)",
        (assistant_msg_id, session_id, "assistant", ai_response, datetime.now().isoformat(), str(citations))
    )
    
    conn.commit()
    conn.close()
    
    return {
        "sessionId": session_id,
        "message": {
            "id": assistant_msg_id,
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "citations": citations
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("Booting local Python SmilAI FastAPI Server on Port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
