import io
import logging
import threading
from dataclasses import dataclass, field
from typing import List, Any
from PIL import Image, UnidentifiedImageError
import numpy as np

@dataclass
class OCRBlock:
    text: str
    confidence: float
    bbox: List[Any]

@dataclass
class OCRResult:
    text: str
    average_confidence: float
    blocks: List[OCRBlock]
    engine: str
    preprocessing: bool

logger = logging.getLogger(__name__)

class OCRProvider:
    def __init__(self):
        self.reader = None
        self.initialized = False
        self.initialization_attempted = False
        self._lock = threading.Lock()

    def initialize(self):
        if self.initialized or self.initialization_attempted:
            return
            
        with self._lock:
            # Double-checked locking
            if self.initialized or self.initialization_attempted:
                return
                
            try:
                import easyocr
                import torch
                
                # Enable GPU if torch detects CUDA
                use_gpu = torch.cuda.is_available()
                
                logger.info(f"Booting up Offline EasyOCR Engine (en, hi). GPU Enabled: {use_gpu}...")
                self.reader = easyocr.Reader(['en', 'hi'], gpu=use_gpu)
                self.initialized = True
                logger.info("EasyOCR loaded successfully.")
            except ImportError:
                logger.error("easyocr or torch is not installed.")
                self.reader = None
                self.initialized = False
                self.initialization_attempted = True
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR: {e}")
                self.reader = None
                self.initialized = False
                self.initialization_attempted = True

    def health(self) -> dict:
        status = "healthy" if self.initialized and self.reader else "uninitialized"
        if not self.reader and self.initialization_attempted:
            status = "error"
        return {
            "status": status,
            "engine": "easyocr",
            "languages": ["en", "hi"] if self.reader else []
        }

    def _preprocess_image(self, img_np: np.ndarray) -> np.ndarray:
        """Applies grayscale and adaptive thresholding to improve OCR accuracy on scans."""
        try:
            import cv2
            # Convert to grayscale
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            # Apply adaptive thresholding to handle uneven lighting in scanned notes
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            # EasyOCR works best with 3-channel images, so convert back
            processed = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
            return processed
        except ImportError:
            logger.warning("cv2 (OpenCV) is not installed, skipping image preprocessing.")
            return img_np
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return img_np

    def extract_text(self, image_data: bytes) -> OCRResult:
        self.initialize()
        
        if not self.reader:
            logger.warning("OCR is called but EasyOCR is not available.")
            return OCRResult(text="", average_confidence=0.0, blocks=[], engine="easyocr", preprocessing=False)

        try:
            # Validate payload size (max 20MB)
            if len(image_data) > 20 * 1024 * 1024:
                raise ValueError(f"Image too large: {len(image_data)} bytes. Max allowed is 20MB.")
                
            # Convert bytes to PIL Image
            try:
                image = Image.open(io.BytesIO(image_data))
            except UnidentifiedImageError:
                raise ValueError("Uploaded file is not a valid image format supported by PIL.")
                
            # Validate dimensions to prevent OOM
            MAX_DIMENSION = 8000
            if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
                raise ValueError(f"Image dimensions too large: {image.width}x{image.height}. Max allowed is {MAX_DIMENSION}px.")

            image = image.convert('RGB')
            img_np = np.array(image)
            
            # Apply Preprocessing (Step 2)
            img_np = self._preprocess_image(img_np)
            
            # readtext returns a list of tuples: (bounding_box, text, confidence)
            # We use paragraph=True to group text blocks logically
            results = self.reader.readtext(img_np, paragraph=True)
            
            blocks = []
            total_confidence = 0.0
            
            for result in results:
                if len(result) == 3:
                    bbox, text, conf = result
                elif len(result) == 2:
                    bbox, text = result
                    conf = 1.0  # Fallback if confidence is omitted
                else:
                    continue
                    
                blocks.append(OCRBlock(text=text, confidence=float(conf), bbox=bbox))
                total_confidence += float(conf)
                
            extracted_text = "\n\n".join([b.text for b in blocks])
            avg_conf = total_confidence / len(blocks) if blocks else 0.0
            
            return OCRResult(
                text=extracted_text,
                average_confidence=avg_conf,
                blocks=blocks,
                engine="easyocr",
                preprocessing=True
            )
            
        except Exception as e:
            import sys
            has_gpu = False
            if 'torch' in sys.modules:
                import torch
                has_gpu = torch.cuda.is_available()
                
            img_w = image.width if 'image' in locals() else "Unknown"
            img_h = image.height if 'image' in locals() else "Unknown"
            size_mb = len(image_data) / (1024 * 1024)
                
            logger.error(
                f"OCR extraction failed\n"
                f"Engine: EasyOCR\n"
                f"GPU: {has_gpu}\n"
                f"Image: {img_w}x{img_h} ({size_mb:.2f} MB)\n"
                f"Exception: {e}"
            )
            return OCRResult(text="", average_confidence=0.0, blocks=[], engine="easyocr", preprocessing=False)

# Singleton instance
ocr_provider = OCRProvider()
