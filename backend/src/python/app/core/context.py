from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class LanguageContext:
    """
    Configuration for inbound and outbound text translation/normalization.
    Immutable to prevent side-effects across the pipeline.
    """
    source_locale: str       # e.g., 'te-IN'
    target_locale: str       # e.g., 'en-US'
    script: str              # e.g., 'telu'
    rtl: bool                # e.g., False

@dataclass(frozen=True)
class UserContext:
    """
    User details for the current request.
    """
    user_id: str
    role: str                # e.g., 'student' or 'teacher'
    persona: str             # e.g., 'teacher', 'storyteller'

@dataclass(frozen=True)
class AcademicContext:
    """
    Educational context for the current request, used for routing glossaries and prompts.
    """
    subject: str             # e.g., 'Science'
    grade: str               # e.g., 'Class 10'
    organization: Optional[str] = None

@dataclass(frozen=True)
class RequestContext:
    """
    The unified context object flowing through the SmilAI architecture.
    """
    user: UserContext
    language: LanguageContext
    academic: AcademicContext
