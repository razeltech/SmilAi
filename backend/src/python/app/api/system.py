from fastapi import APIRouter
from ..core.config import active_profile
from ..core.capabilities import capabilities

router = APIRouter(prefix="/system", tags=["System"])

@router.get("/health")
def health_check():
    """
    Returns the overall health and capabilities of the platform.
    Used by the frontend to selectively enable/disable UI features.
    """
    status = capabilities.to_dict()
    status["deployment"] = active_profile.__class__.__name__
    return status
