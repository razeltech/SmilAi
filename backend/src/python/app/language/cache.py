from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..core.providers import BaseProvider
from ..core.context import RequestContext
import hashlib

class CacheProvider(BaseProvider, ABC):
    """
    Abstract Base Class for translation caching (SQLite, Redis, etc).
    """

    @abstractmethod
    def get(self, text: str, context: RequestContext) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, text: str, translated: str, context: RequestContext) -> None:
        pass

class SQLiteCacheProvider(CacheProvider):
    def initialize(self) -> None:
        pass

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "engine": "sqlite"}

    def capabilities(self) -> Dict[str, Any]:
        return {"persistent": True}

    def _generate_key(self, text: str, context: RequestContext) -> str:
        key_str = f"{context.language.source_locale}:{context.language.target_locale}:{text}"
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

    def get(self, text: str, context: RequestContext) -> Optional[str]:
        # Stub implementation
        return None

    def set(self, text: str, translated: str, context: RequestContext) -> None:
        # Stub implementation
        pass
