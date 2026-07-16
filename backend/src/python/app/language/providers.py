from abc import ABC, abstractmethod
from typing import Dict, Any
from ..core.providers import BaseProvider
from ..core.context import RequestContext

class LanguageProvider(BaseProvider, ABC):
    """
    Abstract Base Class for translation models (IndicTrans2, etc).
    """

    @abstractmethod
    def translate(self, text: str, context: RequestContext) -> str:
        """
        Translates text based on the locale specified in context.language.
        """
        pass

class IndicTransProvider(LanguageProvider):
    """
    Primary translation provider using IndicTrans2 for high-accuracy educational context.
    """
    def __init__(self, model_size: str = "distilled"):
        self.model_size = model_size

    def initialize(self) -> None:
        pass

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "engine": "indictrans2", "size": self.model_size}

    def capabilities(self) -> Dict[str, Any]:
        return {"engine": "indictrans2", "offline": True}

    def translate(self, text: str, context: RequestContext) -> str:
        # Stub implementation
        return text
