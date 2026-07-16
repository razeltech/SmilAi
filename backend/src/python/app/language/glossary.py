from ..core.context import RequestContext

class Glossary:
    def apply(self, text: str, context: RequestContext) -> str:
        # Stub: Return text unmodified.
        # Future: apply subject-specific replacements (e.g. Heart -> హృదయం for Medical)
        return text
