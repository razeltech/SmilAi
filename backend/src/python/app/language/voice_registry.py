from typing import Optional
from ..core.context import RequestContext

class VoiceRegistry:
    """
    Maps language, persona, gender, and deployment profile to a specific voice_id.
    Isolates TTS Engine from language-awareness.
    """
    def __init__(self):
        self.mappings = {
            "te-IN:teacher:female:lite": "piper_telugu_female_1",
            "te-IN:teacher:female:pro": "parler_telugu_female_v1",
            "en-US:teacher:female:lite": "piper_english_amy",
            "en-US:teacher:female:pro": "parler_english_amy_v1",
        }

    def get_voice_id(self, context: RequestContext) -> Optional[str]:
        # Example deployment profile extraction (mocked)
        profile = "lite" 

        key = f"{context.language.source_locale}:{context.user.persona}:female:{profile}"
        return self.mappings.get(key, "default_voice_id")
