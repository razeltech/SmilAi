import sqlite3
import time
import json
import os
import re
import logging
import asyncio
import httpx
from datetime import datetime

from ..database.connection import get_db_connection
from ..database.vector_db import VectorDB
from ..rag.ingest import embedding_model
from ..learning_engine.engine import LearningEngine

logger = logging.getLogger(__name__)

MEMORY_CONFIDENCE_THRESHOLD = 0.70
VOICE_PROMPT_VERSION = "2026_07_v2"

# Ollama models and endpoint
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
LLM_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")

class RewriteReason:
    NO_CHANGE = "no_change"
    LLM = "llm_rewrite"
    TIMEOUT = "timeout_fallback"
    EMPTY_HISTORY = "empty_history_fallback"
    JSON_PARSE_FAILED = "json_parse_failed"

from ..rag.prompts import MEMORY_EXTRACTOR_PROMPT

def extract_first_json_array(text: str) -> str:
    """Extracts the first matching JSON array from text using brace-counting."""
    start = text.find("[")
    if start == -1:
        return ""
    count = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "[":
            count += 1
        elif char == "]":
            count -= 1
            if count == 0:
                return text[start:idx+1]
    return ""

async def extract_student_memory(user_msg: str, assistant_reply: str, student_id: str, subject_id: str):
    """
    Asynchronous background task to extract student profile attributes from a conversation turn
    and save/reinforce them in SQLite and ChromaDB.
    """
    # 1. Clean inputs to prevent prompt pollution
    user_clean = user_msg.strip()
    assistant_clean = assistant_reply.strip()
    
    # Bypass extraction for very short social greetings
    ignored = {"hi", "hello", "thanks", "thank you", "ok", "okay", "bye", "goodbye"}
    if user_clean.lower().replace("?", "").replace("!", "").strip() in ignored:
        return

    # 2. Invoke lightweight analyzer prompt
    user_prompt = f"""Student: {user_clean}

Teacher: {assistant_clean}

Extracted Memory candidates (JSON format):"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": MEMORY_EXTRACTOR_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:
        async def fetch_memory():
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(OLLAMA_URL, json=payload)
                if response.status_code == 200:
                    return response.json()
                return None

        data = await fetch_memory()
        if data and "message" in data and "content" in data["message"]:
            content = data["message"]["content"].strip()
            json_str = extract_first_json_array(content)
            if json_str:
                try:
                    candidates = json.loads(json_str)
                    if not isinstance(candidates, list):
                        candidates = [candidates]
                        
                    for item in candidates:
                        # Extract metrics
                        conf = float(item.get("confidence", 1.0))
                        if conf < MEMORY_CONFIDENCE_THRESHOLD:
                            continue
                            
                        m_type = item.get("type", "ACADEMIC").upper()
                        if m_type not in {'ACADEMIC', 'BEHAVIOUR', 'PREFERENCE', 'PROFILE', 'GOAL'}:
                            m_type = 'ACADEMIC'
                            
                        concept = item.get("concept", "").strip().lower()
                        details = item.get("details", "").strip()
                        
                        if not concept or not details:
                            continue
                            
                        # Save/Reinforce memory in SQLite
                        conn = get_db_connection()
                        existing = None
                        try:
                            existing = conn.execute(
                                "SELECT details, confidence, observation_count FROM student_memory WHERE student_id = ? AND subject_id = ? AND memory_type = ? AND concept = ?",
                                (student_id, subject_id, m_type, concept)
                            ).fetchone()
                            
                            now_str = datetime.utcnow().isoformat()
                            
                            if existing:
                                existing_conf = float(existing["confidence"])
                                existing_details = existing["details"]
                                # Reinforce confidence
                                new_conf = min(0.95, existing_conf + (1.0 - existing_conf) * 0.2)
                                new_count = existing["observation_count"] + 1
                                
                                # Merge details if new details are not already present (avoiding duplicates)
                                if details.lower() not in existing_details.lower():
                                    merged_details = f"{existing_details}; {details}"
                                else:
                                    merged_details = existing_details
                                    
                                conn.execute(
                                    "UPDATE student_memory SET details = ?, confidence = ?, observation_count = ?, updated_at = ? WHERE student_id = ? AND subject_id = ? AND memory_type = ? AND concept = ?",
                                    (merged_details, new_conf, new_count, now_str, student_id, subject_id, m_type, concept)
                                )
                                final_conf = new_conf
                                details = merged_details  # Update details variable to embed the merged text below
                            else:
                                conn.execute(
                                    "INSERT INTO student_memory (student_id, subject_id, memory_type, concept, details, confidence, observation_count, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    (student_id, subject_id, m_type, concept, details, conf, 1, now_str)
                                )
                                final_conf = conf
                            conn.commit()
                        except Exception as sqle:
                            logger.error(f"SQLite student_memory upsert error: {sqle}")
                            continue
                        finally:
                            conn.close()

                        # Write/Upsert memory embedding to ChromaDB
                        try:
                            collection = VectorDB.get_collection("student_memory")
                            memory_id = f"{student_id}_{subject_id}_{m_type}_{concept}"
                            embedding = embedding_model.encode([f"{concept}: {details}"]).tolist()[0]
                            
                            collection.upsert(
                                ids=[memory_id],
                                embeddings=[embedding],
                                documents=[f"{concept}: {details}"],
                                metadatas=[{
                                    "student_id": student_id,
                                    "subject_id": subject_id,
                                    "memory_type": m_type,
                                    "concept": concept
                                }]
                            )
                            logger.info(f"Student Memory Upsert Completed: {m_type} | {concept} (conf={final_conf:.2f})")
                            
                            # If it's an academic concept, also route to the Learning Engine to update Concept Mastery
                            if m_type == 'ACADEMIC':
                                LearningEngine.record_event(
                                    student_id=student_id,
                                    subject_id=subject_id,
                                    event_type="chat_interaction",
                                    payload={"concept": concept, "score": float(final_conf)}
                                )
                                
                        except Exception as ve:
                            logger.error(f"ChromaDB student_memory collection upsert error: {ve}")
                except Exception as pe:
                    logger.error(f"Failed to parse memory JSON list: {pe}. Content: {content}")
    except Exception as e:
        logger.error(f"Exception during background student memory extraction: {e}")

def get_relevant_memories(student_id: str, subject_id: str, query: str) -> str:
    """
    Performs semantic vector search on student_memory Chroma collection,
    buckets by category, and formats a balanced student profile text block.
    """
    rows = []
    
    try:
        collection = VectorDB.get_collection("student_memory")
        query_embedding = embedding_model.encode([query]).tolist()[0]
        
        # Query top 10 relevant items
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=10,
            where={
                "$and": [
                    {"student_id": student_id},
                    {"subject_id": subject_id}
                ]
            }
        )
        
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        # Map concept -> distance
        distance_map = {}
        for idx, meta in enumerate(metadatas):
            concept_key = f"{meta.get('memory_type')}_{meta.get('concept')}"
            if idx < len(distances):
                distance_map[concept_key] = distances[idx]
        
        if metadatas:
            conn = get_db_connection()
            try:
                for meta in metadatas:
                    m_type = meta.get("memory_type")
                    m_concept = meta.get("concept")
                    row = conn.execute(
                        "SELECT memory_type, concept, details, confidence, observation_count, updated_at FROM student_memory WHERE student_id = ? AND subject_id = ? AND memory_type = ? AND concept = ?",
                        (student_id, subject_id, m_type, m_concept)
                    ).fetchone()
                    if row:
                        row_dict = dict(row)
                        
                        # Cosine similarity = 1.0 - distance
                        concept_key = f"{m_type}_{m_concept}"
                        dist = distance_map.get(concept_key, 1.0)
                        similarity = 1.0 - dist
                        
                        # Recency score based on hours decay
                        try:
                            dt = datetime.fromisoformat(row["updated_at"])
                            hours_since = (datetime.utcnow() - dt).total_seconds() / 3600.0
                            recency = 1.0 / (1.0 + hours_since / 24.0)
                        except Exception:
                            recency = 0.5
                            
                        conf = float(row_dict.get("confidence", 0.5))
                        obs_cnt = float(row_dict.get("observation_count", 1))
                        obs_score = min(1.0, obs_cnt / 10.0)
                        
                        # Scoring: 50% similarity, 20% confidence, 20% observation weight, 10% recency
                        row_dict["score"] = 0.5 * similarity + 0.2 * conf + 0.2 * obs_score + 0.1 * recency
                        rows.append(row_dict)
            except Exception as sqle:
                logger.error(f"Failed to load memory rows from SQLite: {sqle}")
            finally:
                conn.close()
    except Exception as e:
        logger.error(f"Vector search failed for student memory: {e}")

    # Fallback: load highest confidence memories from SQLite directly
    if not rows:
        conn = get_db_connection()
        try:
            fallback_rows = conn.execute(
                "SELECT memory_type, concept, details, confidence, observation_count, updated_at FROM student_memory WHERE student_id = ? AND subject_id = ? ORDER BY confidence DESC, observation_count DESC LIMIT 5",
                (student_id, subject_id)
            ).fetchall()
            for r in fallback_rows:
                row_dict = dict(r)
                row_dict["score"] = float(row_dict.get("confidence", 0.5))
                rows.append(row_dict)
        except Exception as sqle:
            logger.error(f"SQLite memory fallback loading failed: {sqle}")
        finally:
            conn.close()

    if not rows:
        return ""

    # Sort rows by comprehensive score descending
    rows.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    # Bucket elements by category
    buckets = {"PROFILE": [], "GOAL": [], "PREFERENCE": [], "ACADEMIC": [], "BEHAVIOUR": []}
    for row in rows:
        m_type = row["memory_type"]
        if m_type in buckets:
            buckets[m_type].append(f"{row['concept']}: {row['details']}")

    # Build category-balanced profile
    selected = []
    if buckets["PROFILE"]:
        selected.append(f"- PROFILE: {buckets['PROFILE'][0]}")
    if buckets["GOAL"]:
        selected.append(f"- GOAL: {buckets['GOAL'][0]}")
    if buckets["PREFERENCE"]:
        selected.append(f"- PREFERENCE: {buckets['PREFERENCE'][0]}")
        
    academic_behaviour = buckets["ACADEMIC"] + buckets["BEHAVIOUR"]
    for item in academic_behaviour[:2]:
        selected.append(f"- ACADEMIC/BEHAVIOUR: {item}")

    if not selected:
        return ""

    profile_block = "\n".join(selected)
    return f"""## STUDENT PROFILE MEMORY
The following persistent profile information is retrieved from the student's historical learning logs. Customize your explanations, pace, and analogies to align with this student's profile:
{profile_block}
"""
