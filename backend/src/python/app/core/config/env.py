import os
import logging
from .profiles.lite import lite_profile
from .profiles.standard import standard_profile
from .profiles.pro import pro_profile

logger = logging.getLogger(__name__)

# Determine the active profile from the environment variable DEPLOYMENT_MODE
_mode = os.environ.get("DEPLOYMENT_MODE", "standard").strip().lower()

if _mode == "lite":
    active_profile = lite_profile
elif _mode == "pro":
    active_profile = pro_profile
else:
    active_profile = standard_profile

logger.info(f"Loaded Deployment Profile: {_mode.upper()} (Target: {active_profile.target_ram} / {active_profile.target_gpu})")
