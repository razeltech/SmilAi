from ..base import DeploymentProfile

pro_profile = DeploymentProfile(
    whisper_model="small.en",
    embedding_model="BAAI/bge-large-en-v1.5",
    llm_model="qwen2.5:14b",
    tts_engine="parler",
    
    enable_voice=True,
    enable_memory=True,
    enable_projects=True,
    enable_translation=True, # Will unlock in v1.4
    enable_assessments=True,
    enable_assignments=True,
    enable_document_upload=True,
    
    max_context_length=16384,
    max_chunk_size=1500,
    max_upload_size_mb=200,
    
    target_ram="64 GB",
    target_gpu="RTX 4090 (24GB VRAM)"
)
