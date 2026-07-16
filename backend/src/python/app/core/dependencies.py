from fastapi import Header, Query, Depends
from typing import Optional
from .context import RequestContext, UserContext, LanguageContext, AcademicContext

def get_request_context(
    x_user_locale: str = Header("en-US"),
    x_user_persona: str = Header("teacher"),
    user_id: str = Header("student_123"), # Mocked for now; usually from JWT
    subject_id: str = Header("sub_123"),
    grade: str = Header("Class 10")
) -> RequestContext:
    """
    Constructs the immutable RequestContext from HTTP headers.
    This eliminates the need for complex middleware and allows easy injection into any router.
    """
    return RequestContext(
        user=UserContext(
            user_id=user_id,
            role="student",
            persona=x_user_persona
        ),
        language=LanguageContext(
            source_locale=x_user_locale,
            target_locale="en-US", # English Core is always the target internally
            script="latn",         # Stubbed for now
            rtl=False
        ),
        academic=AcademicContext(
            subject=subject_id,
            grade=grade
        )
    )
