import io
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class OCRProvider:
    def __init__(self):
        self.reader = None
        self.initialized = False

    def initialize(self):
        if self.initialized:
            return
        
        try:
            import easyocr
            import torch
            
            # Enable GPU if torch detects CUDA
            use_gpu = torch.cuda.is_available()
            
            logger.info(f"Booting up Offline EasyOCR Engine (en, hi, te). GPU Enabled: {use_gpu}...")
            self.reader = easyocr.Reader(['en', 'hi', 'te'], gpu=use_gpu)
            self.initialized = True
            logger.info("EasyOCR loaded successfully.")
        except ImportError:
            logger.error("easyocr or torch is not installed.")
            self.reader = None
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None

    def extract_text(self, image_data: bytes) -> str:
        self.initialize()
        
        if not self.reader:
            logger.warning("OCR is called but EasyOCR is not available.")
            return ""

        try:
            # Convert bytes to PIL Image, then to numpy array for EasyOCR
            image = Image.open(io.BytesIO(image_data)).convert('RGB')
            img_np = np.array(image)
            
            # readtext returns a list of tuples: (bounding_box, text, confidence)
            # We use paragraph=True to group text blocks logically
            results = self.reader.readtext(img_np, paragraph=True)
            
            # Join the extracted text blocks. For paragraph=True, result is (bbox, text)
            extracted = "\n\n".join([text for (_, text) in results])
            return extracted.strip()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

# Singleton instance
ocr_provider = OCRProvider()
