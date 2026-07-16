from .providers import IndicTransProvider
from .cache import SQLiteCacheProvider
from .service import LanguageService
from .adapter import LanguageAdapter

# Singleton instances
_cache_provider = SQLiteCacheProvider()
_language_provider = IndicTransProvider()
_language_service = LanguageService(provider=_language_provider, cache=_cache_provider)
_language_adapter = LanguageAdapter(service=_language_service)

def get_language_adapter() -> LanguageAdapter:
    return _language_adapter
