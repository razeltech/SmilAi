import httpx
import json
import os
import time
import asyncio
import logging

from .prompts import SMILEY_SYSTEM_PROMPT, SEARCH_REWRITER_PROMPT
from .prompt_builder import PROMPT_BUILDER

from ..core.config import active_profile

from .providers import OllamaProvider

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("OLLAMA_MODEL", active_profile.llm_model)

# Default global provider
default_provider = OllamaProvider(OLLAMA_URL)

async def generate_rag_response_stream(
    query: str, 
    retrieved_chunks: list, 
    history: list = None, 
    is_conversational: bool = False,
    student_id: str = "",
    subject_id: str = "",
    metrics_out: dict = None,
    provider = None
):
    """
    Streams the response directly using the provided InferenceProvider (defaults to Ollama).
    Uses PromptBuilder to assemble the payload, and outputs tokens.
    """
    if provider is None:
        provider = default_provider
        
    # 1. Select the dynamic temperature and prompt mode
    temp = 0.7 if is_conversational else 0.3
    
    # 2. Retrieve student profile card if active and write memory count to metrics
    profile_card = ""
    if student_id and subject_id:
        try:
            from ..memory.service import get_relevant_memories
            profile_card = get_relevant_memories(student_id, subject_id, query)
            if profile_card and metrics_out is not None:
                bullets = [line for line in profile_card.splitlines() if line.strip().startswith("-")]
                metrics_out["memory_count"] = len(bullets)
        except Exception as e:
            logging.error(f"Failed to fetch student memories: {e}")

    # 3. Assemble prompt payload using global singleton builder
    messages = PROMPT_BUILDER.build(
        query=query,
        retrieved_chunks=retrieved_chunks,
        history=history,
        is_conversational=is_conversational,
        profile_card=profile_card
    )
    
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "options": {
            "temperature": temp,
            "num_ctx": 8192,
            "stop": ["Student:", "Teacher:", "[Student]:", "[Teacher]:"]
        }
    }
    
    # 4. Stream from Provider
    async for chunk in provider.generate_stream(payload):
        yield chunk

class RewriteReason:
    NO_CHANGE = "no_change"
    LLM = "llm_rewrite"
    TIMEOUT = "timeout_fallback"
    EMPTY_HISTORY = "empty_history_fallback"
    JSON_PARSE_FAILED = "json_parse_failed"

FOLLOWUP_PATTERNS = {
    "it", "this", "that", "those", "these", "they", "them", "again", 
    "another", "continue", "further", "more", "second", "third", 
    "previous", "former", "latter", "difference", "compare", "advantages", 
    "disadvantages", "example", "simplify", "elaborate", "clarify"
}

# (SEARCH_REWRITER_PROMPT imported from .prompts)

def extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return ""
    count = 0
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "{":
            count += 1
        elif char == "}":
            count -= 1
            if count == 0:
                return text[start:idx+1]
    return ""

def get_academic_history(history: list) -> list:
    """
    Extracts only academic user turns from the history (ignoring social greetings/closures).
    Returns the last 2 user turns.
    """
    if not history:
        return []
    ignored_messages = {"hi", "hello", "thanks", "thank you", "ok", "okay", "bye", "goodbye", "yes", "no"}
    user_turns = []
    for h in history:
        if h.get("role") == "user":
            content_clean = h.get("content", "").strip().lower().replace("?", "").replace("!", "").replace(".", "").strip()
            if content_clean not in ignored_messages:
                user_turns.append(h)
    return user_turns[-2:]

def needs_rewrite(query: str, history: list) -> bool:
    if not history:
        return False
    cleaned = query.strip().lower()
    words = set(cleaned.replace("?", "").replace("!", "").replace(".", "").split())
    if words.intersection(FOLLOWUP_PATTERNS):
        return True
    return False

async def prepare_search_query(query: str, history: list) -> dict:
    """
    Analyzes user query and decides whether to rewrite it into a standalone search query.
    Returns a dict with query, rewritten flag, rewrite_skipped flag, reason, and time taken.
    """
    start_time = time.perf_counter()
    
    # 1. Cheap Heuristics check
    if not history:
        return {
            "query": query,
            "rewritten": False,
            "rewrite_skipped": True,
            "reason": RewriteReason.EMPTY_HISTORY,
            "rewrite_time_ms": 0
        }
        
    if not needs_rewrite(query, history):
        return {
            "query": query,
            "rewritten": False,
            "rewrite_skipped": True,
            "reason": RewriteReason.NO_CHANGE,
            "rewrite_time_ms": 0
        }
        
    # 2. Invoke lightweight rewriter model using academic user turns only
    academic_history = get_academic_history(history)
    if not academic_history:
        return {
            "query": query,
            "rewritten": False,
            "rewrite_skipped": True,
            "reason": RewriteReason.EMPTY_HISTORY,
            "rewrite_time_ms": 0
        }

    history_text = "\n".join([f"Student Question: {h['content']}" for h in academic_history])
    user_prompt = f"""Conversation History:
{history_text}

Latest Student Message: {query}

Standalone Search Query:"""

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SEARCH_REWRITER_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "stop": ["\n"]
        }
    }
    
    # Perform rewriting under a 3.0s timeout
    try:
        async def fetch_rewrite():
            from .inference import default_provider
            data = await default_provider.generate(payload)
            if data:
                return data
            return None
                
        data = await asyncio.wait_for(fetch_rewrite(), timeout=3.0)
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        
        if data and "message" in data and "content" in data["message"]:
            content = data["message"]["content"].strip()
            # Extract JSON cleanly using brace-counting parser
            json_str = extract_first_json_object(content)
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    prepared_query = parsed.get("query", query).strip()
                    rewritten = (prepared_query != query)
                    return {
                        "query": prepared_query,
                        "rewritten": rewritten,
                        "rewrite_skipped": False,
                        "reason": RewriteReason.LLM if rewritten else RewriteReason.NO_CHANGE,
                        "rewrite_time_ms": latency_ms
                    }
                except Exception as e:
                    logging.exception("Failed to parse JSON rewrite response")
            # JSON parsing failed fallback
            return {
                "query": query,
                "rewritten": False,
                "rewrite_skipped": False,
                "reason": RewriteReason.JSON_PARSE_FAILED,
                "rewrite_time_ms": latency_ms
            }
    except asyncio.TimeoutError:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "query": query,
            "rewritten": False,
            "rewrite_skipped": False,
            "reason": RewriteReason.TIMEOUT,
            "rewrite_time_ms": latency_ms
        }
    except Exception as e:
        logging.exception("Exception in prepare_search_query")
        
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return {
        "query": query,
        "rewritten": False,
        "rewrite_skipped": False,
        "reason": RewriteReason.NO_CHANGE,
        "rewrite_time_ms": latency_ms
    }
