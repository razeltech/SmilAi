from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    """
    Base Provider interface for all SmilAI AI subsystems.
    Enforces a consistent contract across Inference, Language, Voice, and Embedding engines.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Loads models into memory or initializes connections.
        Should handle local_files_only checks for offline-first deployments.
        """
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """
        Returns the health status of the provider.
        Expected to return {"status": "ok" | "error" | "unavailable", ...}
        """
        pass

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """
        Returns the supported capabilities of this provider instance.
        (e.g., supported languages, context windows, model variants)
        """
        pass
