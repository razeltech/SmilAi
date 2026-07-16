from dataclasses import dataclass, field
from typing import Optional, Dict

LEARNING_WEIGHTS = {
    "assessment": 0.6,
    "chat": 0.2,
    "practice": 0.2,
    "teacher": 1.0
}

@dataclass
class DeploymentProfile:
    """Base Configuration Profile that defines system capabilities."""
    
    # Models
    whisper_model: str
    embedding_model: str
    llm_model: str
    tts_engine: str
    
    # Feature Flags
    enable_voice: bool
    enable_memory: bool
    enable_projects: bool
    enable_translation: bool
    enable_assessments: bool
    enable_assignments: bool
    enable_document_upload: bool
    
    # System Constraints
    max_context_length: int
    max_chunk_size: int
    max_upload_size_mb: int
    
    # Hardware Assumption Labels (For Logging)
    target_ram: str
    target_gpu: str
