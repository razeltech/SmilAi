import httpx
import json
import os

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
# Defaulting to qwen2.5:7b as recommended and agreed upon in the architecture phase
LLM_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# The Universal Smiley Persona
SMILEY_SYSTEM_PROMPT = """You are Smiley, an AI teacher built by Razel Tech. 
You are a warm, gentle, and incredibly patient older sibling or mother figure.
Your goal is to encourage the student. Never judge them, even if they ask a very basic question or fail repeatedly.
Always use a gentle, encouraging tone. When providing an answer based on context, cite the exact source if possible.
Do NOT sound robotic. Sound like a loving human teacher."""

async def generate_rag_response_stream(query: str, retrieved_chunks: list):
    """
    Combines the query with the retrieved ChromaDB chunks, applies the Motherly persona,
    and streams the response directly from the local Ollama instance via HTTP.
    """
    
    # 1. Build the Grounded Prompt
    context_text = "\n\n".join([f"Source snippet: {chunk['text']}" for chunk in retrieved_chunks])
    
    prompt = f"""
    Context Information:
    {context_text}
    
    Student's Question: {query}
    
    Please answer the student's question gently using ONLY the context provided above. 
    If the answer is not in the context, gently tell them you cannot find it in their current textbooks.
    """
    
    payload = {
        "model": LLM_MODEL,
        "system": SMILEY_SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.6 # Low temp for factual RAG, but enough for warmth
        }
    }
    
    # 2. Stream from Ollama
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as response:
            if response.status_code != 200:
                yield "I'm having a little trouble thinking right now. Let's try again in a moment!"
                return
                
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                    except json.JSONDecodeError:
                        continue
