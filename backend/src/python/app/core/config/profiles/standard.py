from ..base import DeploymentProfile

standard_profile = DeploymentProfile(
    whisper_model="base.en",
    embedding_model="BAAI/bge-small-en-v1.5", 
    llm_model="qwen2.5:7b-instruct",
    tts_engine="parler",
    
    enable_voice=True,
    enable_memory=True, # Active extraction of student history
    enable_projects=True,
    enable_translation=False, # Wait for v1.4
    enable_assessments=True,
    enable_assignments=True,
    enable_document_upload=True,
    
    max_context_length=8192,
    max_chunk_size=1000,
    max_upload_size_mb=50,
    
    target_ram="16 GB",
    target_gpu="RTX 3060 (12GB VRAM)"
)
