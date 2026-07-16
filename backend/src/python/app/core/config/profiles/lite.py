from ..base import DeploymentProfile

lite_profile = DeploymentProfile(
    whisper_model="tiny.en",
    embedding_model="BAAI/bge-small-en-v1.5",
    llm_model="qwen2.5:3b",
    tts_engine="piper",
    
    enable_voice=True, # Voice is available via Piper & Whisper Tiny
    enable_memory=False, # Disable complex memory extraction
    enable_projects=False, # Simplify subjects for light hardware
    enable_translation=False, # No IndicTrans loaded
    enable_assessments=True,
    enable_assignments=True,
    enable_document_upload=True,
    
    max_context_length=2048, # Small context window for 3B models
    max_chunk_size=500, # Smaller RAG chunks
    max_upload_size_mb=10, # Keep docs small
    
    target_ram="8 GB",
    target_gpu="None (CPU Only)"
)
