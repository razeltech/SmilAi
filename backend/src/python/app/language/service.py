from .normalizer import TextNormalizer
from .glossary import Glossary
from .providers import LanguageProvider
from .cache import CacheProvider
from ..core.context import RequestContext

class LanguageService:
    """
    Orchestrates the language pipeline.
    Flow: Normalize -> Cache -> Glossary -> Translate -> Post-Process
    """
    def __init__(self, provider: LanguageProvider, cache: CacheProvider):
        self.normalizer = TextNormalizer()
        self.glossary = Glossary()
        self.provider = provider
        self.cache = cache

    def process_inbound(self, raw_text: str, context: RequestContext) -> str:
        """Translates user text to English Core."""
        # 1. Normalize
        text = self.normalizer.normalize(raw_text)

        # 2. Cache lookup
        cached = self.cache.get(text, context)
        if cached:
            return cached

        # 4. Glossary
        text = self.glossary.apply(text, context)

        # 5. Translate
        if context.language.source_locale == context.language.target_locale:
            translated = text # Passthrough
        else:
            translated = self.provider.translate(text, context)

        # 6. Set Cache
        self.cache.set(text, translated, context)

        return translated

    def process_outbound(self, english_text: str, context: RequestContext) -> str:
        """Translates English Core text back to User's language."""
        if context.language.source_locale == context.language.target_locale:
            return english_text

        cached = self.cache.get(english_text, context)
        if cached:
            return cached

        text = self.glossary.apply(english_text, context)
        translated = self.provider.translate(text, context)
        self.cache.set(english_text, translated, context)

        # Future: Speech Preparation Post-processing (spacing, punctuation for Indic languages)
        return translated
