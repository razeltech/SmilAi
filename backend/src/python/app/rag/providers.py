from abc import ABC, abstractmethod
import httpx
import json
import logging
from typing import AsyncGenerator, Dict, Any

class InferenceProvider(ABC):
    """
    Abstract Base Class for LLM Inference Engines.
    Provides a unified interface so the core logic does not depend on a specific engine (Ollama, vLLM, etc).
    """
    @abstractmethod
    async def generate_stream(self, payload: dict) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def generate(self, payload: dict) -> dict:
        pass

    @abstractmethod
    async def health(self) -> bool:
        pass

    @abstractmethod
    def embeddings_supported(self) -> bool:
        pass

class OllamaProvider(InferenceProvider):
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def generate_stream(self, payload: dict) -> AsyncGenerator[str, None]:
        payload["stream"] = True
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                if response.status_code != 200:
                    yield "I'm having a little trouble thinking right now. Let's try again in a moment!"
                    return
                    
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done") is True:
                                # We can't easily yield dicts in a string generator cleanly without wrapping, 
                                # but for now we just return the string chunks. Metrics extraction is handled separately.
                                pass
                        except json.JSONDecodeError:
                            continue

    async def generate(self, payload: dict) -> dict:
        payload["stream"] = False
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logging.error(f"Ollama generation failed: {e}")
        return {}

    async def health(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
            except Exception:
                return False

    def embeddings_supported(self) -> bool:
        return True
