from .service import LanguageService
from ..core.context import RequestContext

class LanguageAdapter:
    """
    Middleware boundary that wraps inbound and outbound requests.
    """
    def __init__(self, service: LanguageService):
        self.service = service

    def inbound(self, raw_text: str, context: RequestContext) -> str:
        return self.service.process_inbound(raw_text, context)

    def outbound(self, english_text: str, context: RequestContext) -> str:
        return self.service.process_outbound(english_text, context)
