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

# Requirement: pip install indictranstoolkit transformers>=4.51 torch
TOKENIZER_MAX_LENGTH = 512
GENERATION_MAX_NEW_TOKENS = 512

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

    # Primary 13 Supported Languages Mapping for IndicTrans2 in SmilAI
    LANG_MAP = {
        "en": "eng_Latn",
        "hi": "hin_Deva",
        "te": "tel_Telu",
        "ta": "tam_Taml",
        "ml": "mal_Mlym",
        "kn": "kan_Knda",
        "mr": "mar_Deva",
        "gu": "guj_Gujr",
        "pa": "pan_Guru",
        "bn": "ben_Beng",
        "or": "ory_Orya",
        "as": "asm_Beng",
        "ur": "urd_Arab"
    }

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.processor = None
        
        self.current_direction = None
        self.status = "idle"
        
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

    def _unload_locked(self):
        """Internal method to unload the active model. Assumes lock is already held."""
        if self.model:
            logger.info(f"Unloading model {self.current_direction} from {self.device} to free memory...")
            del self.model
            del self.tokenizer
            del self.processor
            self.model = None
            self.tokenizer = None
            self.processor = None
            self.current_direction = None
            self.status = "idle"
            
            if self.device == "cuda":
                import torch
                import gc
                alloc_before = torch.cuda.memory_allocated() / (1024**2)
                gc.collect()
                torch.cuda.empty_cache()
                alloc_after = torch.cuda.memory_allocated() / (1024**2)
                logger.info(f"VRAM freed: {alloc_before:.2f} MB -> {alloc_after:.2f} MB")

    def unload(self):
        """Unload the active model and clear GPU cache to free VRAM."""
        with self._lock:
            self._unload_locked()

    def _get_direction(self, source_language: str, target_language: str) -> str:
        """Determines the required directional model."""
        if source_language == "en" and target_language != "en":
            return "en-indic"
        elif source_language != "en" and target_language == "en":
            return "indic-en"
        return "invalid"

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
                self._unload_locked()
                    
            try:
                self.status = "loading"
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
                from IndicTransToolkit import IndicProcessor
                
                model_id = self.MODELS[direction]
                logger.info(f"Loading IndicTrans2 ({direction}) onto {self.device}...")
                
                self.processor = IndicProcessor(inference=True)
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
                self.status = "healthy"
                logger.info(f"Successfully loaded {model_id}")
                
            except Exception as e:
                self.status = "error"
                logger.error(f"Failed to load model {direction}: {e}")
                self.model = None
                self.tokenizer = None
                self.processor = None
                self.current_direction = None
                raise

    def initialize(self):
        """No preloading. Model will be loaded on the first request to save startup time."""
        pass

    def health(self) -> Dict[str, Any]:
        models_loaded = [self.current_direction] if self.current_direction else []
        return {
            "status": self.status,
            "loaded_model": self.current_direction,
            "device": self.device,
            "models_loaded": models_loaded,
            "cache_strategy": "single_gpu"
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
        direction = self._get_direction(source_language, target_language)
        if direction == "invalid":
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
            
            if not self.model or not self.tokenizer or not self.processor:
                raise RuntimeError("Model failed to load.")
                
            src_lang_code = self.LANG_MAP[source_language]
            tgt_lang_code = self.LANG_MAP[target_language]
            
            import torch
            
            with torch.inference_mode():
                # IndicTransToolkit official preprocessing
                batch_text = self.processor.preprocess_batch([text], src_lang=src_lang_code, tgt_lang=tgt_lang_code)
                
                inputs = self.tokenizer(
                    batch_text, 
                    padding="longest", 
                    truncation=True, 
                    max_length=TOKENIZER_MAX_LENGTH, 
                    return_tensors="pt"
                ).to(self.device)
                
                outputs = self.model.generate(
                    **inputs,
                    use_cache=True,
                    num_beams=5,
                    max_length=GENERATION_MAX_NEW_TOKENS
                )
                
                decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
                # Official postprocessing
                translated_text = self.processor.postprocess_batch(decoded, lang=tgt_lang_code)[0]
                
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
