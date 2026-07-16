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
        return {
            "sqlite": "ok" if self.sqlite else "missing",
            "chroma": "ok" if self.chroma else "missing",
            "ollama": "ok" if self.ollama else "missing",
            "memory": "enabled" if self.memory else "disabled",
            "learning": "enabled" if self.learning else "disabled",
            "analytics": "enabled" if self.analytics else "disabled",
            "voice": "ok" if self.voice else "missing",
            "translation": "enabled" if self.translation else "disabled"
        }

# Global singleton
capabilities = SystemCapabilities()
