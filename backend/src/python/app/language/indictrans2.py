import time
import logging
import threading
from dataclasses import dataclass
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    model_name: str
    latency_ms: float
    success: bool
    error: Optional[str]
    device: str
    direction: str

class IndicTransProvider:
    """
    Standalone Translation Provider using IndicTrans2 (1B).
    Manages VRAM aggressively by keeping only one directional model in GPU memory at a time.
    """
    
    # Model Hub IDs
    MODELS = {
        "en-indic": "ai4bharat/indictrans2-en-indic-1B",
        "indic-en": "ai4bharat/indictrans2-indic-en-1B"
    }

    # ISO Language Maps for IndicTrans2 tokenization
    LANG_MAP = {
        "en": "eng_Latn",
        "te": "tel_Telu",
        "hi": "hin_Deva"
    }

    def __init__(self):
        self.tokenizer = None
        self.model = None
        
        self.current_direction = None
        self.initialization_attempted = False
        
        # Determine optimal device
        import sys
        self.device = "cpu"
        self.has_gpu = False
        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"
                self.has_gpu = True
        except ImportError:
            pass
            
        self._lock = threading.Lock()

    def unload(self):
        """Unload the active model and clear GPU cache to free VRAM."""
        with self._lock:
            if self.model:
                logger.info(f"Unloading model {self.current_direction} from {self.device} to free memory...")
                del self.model
                del self.tokenizer
                self.model = None
                self.tokenizer = None
                self.current_direction = None
                
                if self.device == "cuda":
                    import torch
                    import gc
                    gc.collect()
                    torch.cuda.empty_cache()

    def _load_model(self, direction: str):
        """Internal method to load a model. Unloads current model if a swap is needed."""
        if self.current_direction == direction and self.model is not None:
            return  # Already loaded
            
        # Ensure thread safety during model swapping
        with self._lock:
            # Double check in case another thread loaded it while waiting
            if self.current_direction == direction and self.model is not None:
                return
                
            # Unload existing model if it's different
            if self.model is not None:
                logger.info(f"Swapping models: unloading {self.current_direction}")
                del self.model
                del self.tokenizer
                if self.device == "cuda":
                    import torch
                    import gc
                    gc.collect()
                    torch.cuda.empty_cache()
                    
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                
                model_id = self.MODELS[direction]
                logger.info(f"Loading IndicTrans2 ({direction}) onto {self.device}...")
                
                self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
                # Load in fp16 if on CUDA to save memory
                dtype = torch.float16 if self.device == "cuda" else torch.float32
                
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_id, 
                    trust_remote_code=True,
                    torch_dtype=dtype
                ).to(self.device)
                
                self.model.eval()
                self.current_direction = direction
                self.initialization_attempted = True
                logger.info(f"Successfully loaded {model_id}")
                
            except Exception as e:
                self.initialization_attempted = True
                logger.error(f"Failed to load model {direction}: {e}")
                self.model = None
                self.tokenizer = None
                self.current_direction = None
                raise

    def initialize(self):
        """Pre-warms the provider with en-indic by default if nothing is loaded."""
        if self.model is None and not self.initialization_attempted:
            try:
                self._load_model("en-indic")
            except Exception:
                pass # Exceptions logged in _load_model

    def health(self) -> Dict[str, Any]:
        models_loaded = [self.current_direction] if self.current_direction else []
        return {
            "status": "healthy" if self.model else "uninitialized",
            "loaded_model": self.current_direction,
            "device": self.device,
            "models_loaded": models_loaded,
            "cache_strategy": "single_gpu",
            "initialization_attempted": self.initialization_attempted
        }

    def translate(self, text: str, source_language: str, target_language: str) -> TranslationResult:
        start_time = time.time()
        
        # 1. Validation
        if not text or not text.strip():
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                model_name="none",
                latency_ms=(time.time() - start_time) * 1000,
                success=True,
                error=None,
                device=self.device,
                direction=f"{source_language}->{target_language}"
            )
            
        if source_language not in self.LANG_MAP or target_language not in self.LANG_MAP:
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                model_name="none",
                latency_ms=(time.time() - start_time) * 1000,
                success=False,
                error=f"Unsupported language pair. Supported: {list(self.LANG_MAP.keys())}",
                device=self.device,
                direction=f"{source_language}->{target_language}"
            )

        # Determine required direction
        if source_language == "en" and target_language in ["te", "hi"]:
            direction = "en-indic"
        elif source_language in ["te", "hi"] and target_language == "en":
            direction = "indic-en"
        else:
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                model_name="none",
                latency_ms=(time.time() - start_time) * 1000,
                success=False,
                error="Only English-to-Indic and Indic-to-English directions are currently supported.",
                device=self.device,
                direction=f"{source_language}->{target_language}"
            )

        # 2. Execution
        try:
            # Swap models if necessary
            self._load_model(direction)
            
            if not self.model or not self.tokenizer:
                raise RuntimeError("Model failed to load.")
                
            src_lang_code = self.LANG_MAP[source_language]
            tgt_lang_code = self.LANG_MAP[target_language]
            
            import torch
            
            with torch.no_grad():
                # IndicTrans2 specific tokenization
                batch = self.tokenizer(text, src=src_lang_code, return_tensors="pt")
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                generated_tokens = self.model.generate(
                    **batch,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=5,
                    out_lang=tgt_lang_code
                )
                
                translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
                
            latency_ms = (time.time() - start_time) * 1000
            
            return TranslationResult(
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                model_name=self.MODELS[direction],
                latency_ms=latency_ms,
                success=True,
                error=None,
                device=self.device,
                direction=direction
            )
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            latency_ms = (time.time() - start_time) * 1000
            return TranslationResult(
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                model_name=self.MODELS.get(direction, "unknown"),
                latency_ms=latency_ms,
                success=False,
                error=str(e),
                device=self.device,
                direction=direction
            )

# Singleton instance
translation_provider = IndicTransProvider()
