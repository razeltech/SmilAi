class SystemCapabilities:
    """
    Global registry for subsystem capabilities. 
    Allows the platform to gracefully degrade if certain models or services are missing,
    rather than crashing the entire backend.
    """
    def __init__(self):
        self.sqlite = True          # Core
        self.chroma = True          # Core
        self.ollama = True          # Core
        self.memory = True          # Async task
        self.learning = True        # Async task
        self.analytics = True       # Async task
        self.voice = True           # Can be disabled if models missing
        self.translation = False    # v1.4 feature

    def to_dict(self) -> dict:
        from .config import active_profile
        return {
            "voice": {
                "enabled": self.voice,
                "engine": active_profile.tts_engine,
                "profile": active_profile.__class__.__name__
            },
            "llm": {
                "enabled": self.ollama,
                "engine": "ollama",
                "model": active_profile.llm_model
            },
            "embeddings": {
                "enabled": self.chroma,
                "engine": "chroma",
                "model": active_profile.embedding_model
            },
            "translation": {
                "enabled": self.translation,
                "engine": "none",
                "profile": active_profile.__class__.__name__
            },
            "learning": {
                "enabled": self.learning,
                "engine": "deterministic",
                "profile": active_profile.__class__.__name__
            },
            "database": {
                "enabled": self.sqlite,
                "engine": "sqlite"
            },
            "deployment": active_profile.__class__.__name__
        }

# Global singleton
capabilities = SystemCapabilities()
