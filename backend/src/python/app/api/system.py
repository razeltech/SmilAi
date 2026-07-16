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
    return capabilities.to_dict()

@router.get("/version")
def system_version():
    """
    Returns the version, active git commit, and active profile for deployment debugging.
    """
    return {
        "version": "1.3.5",
        "git": "d3f862c",
        "profile": active_profile.__class__.__name__,
        "build": "release"
    }
