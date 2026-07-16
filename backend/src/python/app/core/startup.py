import logging
from .config import active_profile
from ..database.connection import init_db

logger = logging.getLogger(__name__)

def boot_system():
    """
    Centralized deterministic Startup Manager.
    Loads subsystems based on active_profile.
    """
    logger.info("Initializing SmilAI Startup Manager...")
    
    # 1. Database & Vector DB
    init_db()
    
    # 2. Embedding Model (if needed early)
    if active_profile.embedding_model:
        logger.info(f"Loading embeddings model: {active_profile.embedding_model}")
        from ..rag.ingest import get_embedder
        # Initialize early to avoid cold start
        get_embedder()

    # 3. Voice (Whisper / TTS)
    if active_profile.enable_voice:
        logger.info("Initializing Voice Engine based on profile...")
        from ..api.voice import get_whisper_model, initialize_tts_engine
        
        # Override the defaults in voice.py using active_profile if possible,
        # but for now we just trigger their init.
        # Ideally we update voice.py to use active_profile.whisper_model, etc.
        try:
            get_whisper_model()
            initialize_tts_engine()
        except Exception as e:
            logger.error(f"Voice Engine failed to initialize: {e}")

    logger.info("Startup complete. System is ready.")
