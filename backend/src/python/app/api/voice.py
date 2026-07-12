import os
import uuid
import wave
import io
import urllib.request
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

# Strictly enforce offline local caching for AI models
os.environ["HF_HOME"] = os.environ.get("HF_HOME", "./models/hf_cache")
PIPER_CACHE_DIR = os.path.join(os.environ["HF_HOME"], "piper")
os.makedirs(PIPER_CACHE_DIR, exist_ok=True)

PIPER_VOICE_NAME = "en_GB-alba-medium"
PIPER_ONNX_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/{PIPER_VOICE_NAME}.onnx"
PIPER_JSON_URL = f"{PIPER_ONNX_URL}.json"

router = APIRouter(prefix="/voice", tags=["Voice Engine"])

# Global AI Models
whisper_model = None
parler_model = None
parler_tokenizer = None
piper_voice = None
tts_engine_initialized = False
tts_init_error = ""

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        logger.info("Booting up Local Whisper STT Engine...")
        try:
            from faster_whisper import WhisperModel
            # STT stays on CPU to keep VRAM free for LLM/Parler
            whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
        except ImportError:
            logger.error("faster_whisper is not installed.")
            raise RuntimeError("faster_whisper is not installed. Voice STT unavailable.")
    return whisper_model

def initialize_tts_engine():
    import sys
    logger.error(f"UVICORN WORKER EXEC: {sys.executable}")
    logger.error(f"UVICORN WORKER PATH: {sys.path}")
    global parler_model, parler_tokenizer, piper_voice, tts_engine_initialized, tts_init_error
    if tts_engine_initialized and (parler_model is not None or piper_voice is not None):
        return
    
    logger.info("Booting up Two-Tier TTS Engine...")
    
    # 1. Try Loading Parler-TTS (Indian Accent) on GPU
    try:
        import torch
        if torch.cuda.is_available():
            free_mem, _ = torch.cuda.mem_get_info()
            if free_mem > 2 * 1024 * 1024 * 1024:
                from parler_tts import ParlerTTSForConditionalGeneration
                from transformers import AutoTokenizer
                logger.info("GPU detected with >2GB VRAM. Loading ai4bharat/indic-parler-tts...")
                parler_model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to("cuda")
                parler_tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
                logger.info("Indic Parler-TTS loaded successfully on GPU.")
            else:
                logger.warning(f"Not enough VRAM for Parler-TTS (Free: {free_mem/(1024**3):.2f}GB). Falling back to Piper.")
        else:
            logger.warning("No GPU detected for Parler-TTS. Skipping to fallback.")
    except Exception as e:
        import traceback
        tts_init_error = f"Parler error: {traceback.format_exc()}"
        logger.error(f"Parler-TTS unavailable ({e}). Skipping to fallback.")
        parler_model = None
        parler_tokenizer = None

    # 2. Try Loading Piper (CPU Fallback)
    if parler_model is None:
        try:
            from piper.voice import PiperVoice
            onnx_path = os.path.join(PIPER_CACHE_DIR, f"{PIPER_VOICE_NAME}.onnx")
            json_path = os.path.join(PIPER_CACHE_DIR, f"{PIPER_VOICE_NAME}.onnx.json")
            
            if not os.path.exists(onnx_path):
                logger.info(f"Downloading Piper Fallback Model ({PIPER_VOICE_NAME})...")
                urllib.request.urlretrieve(PIPER_ONNX_URL, onnx_path)
                urllib.request.urlretrieve(PIPER_JSON_URL, json_path)
                logger.info("Piper Download complete.")
                
            piper_voice = PiperVoice.load(onnx_path, config_path=json_path)
            logger.info("Piper TTS Fallback loaded successfully.")
        except Exception as e:
            import traceback
            import sys
            tts_init_error = f"Piper error: {traceback.format_exc()} EXEC: {sys.executable}"
            logger.error(f"Piper TTS Fallback unavailable ({e}).")
        
    tts_engine_initialized = True

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Takes an audio file from the frontend (e.g. WebM or WAV)
    and converts it instantly to text using the local Whisper model.
    """
    os.makedirs("./database/temp_audio", exist_ok=True)
    temp_audio_path = f"./database/temp_audio/{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(temp_audio_path, "wb") as f:
            f.write(await file.read())
            
        model = get_whisper_model()
        segments, info = await asyncio.to_thread(model.transcribe, temp_audio_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        
        return {"text": text.strip(), "language": info.language}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice Recognition Error: {str(e)}")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@router.post("/speak")
def generate_speech(text: str):
    """
    Takes Smiley's text response and generates a beautiful Indian-accented voice using Parler-TTS.
    Falls back to Piper TTS if Parler is unavailable. Returns a WAV audio file.
    """
    initialize_tts_engine()
    
    os.makedirs("./database/temp_audio", exist_ok=True)
    output_path = f"./database/temp_audio/{uuid.uuid4()}_smiley.wav"
    
    try:
        if parler_model and parler_tokenizer:
            # Tier 1: High-Fidelity South Indian Andhra Pradesh Female Voice
            import soundfile as sf
            description = "A gentle female voice with a South Indian Andhra Pradesh accent, speaking clearly and warmly."
            input_ids = parler_tokenizer(description, return_tensors="pt").input_ids.to("cuda")
            prompt_input_ids = parler_tokenizer(text, return_tensors="pt").input_ids.to("cuda")
            
            generation = parler_model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
            audio_arr = generation.cpu().numpy().squeeze()
            
            sf.write(output_path, audio_arr, parler_model.config.sampling_rate, format='wav')
            
        elif piper_voice:
            # Tier 2: Piper CPU Fallback
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2) # 16-bit PCM
                wav_file.setframerate(piper_voice.config.sample_rate)
                piper_voice.synthesize(text, wav_file)
                
        else:
            raise RuntimeError(f"Models: parler={type(parler_model)}, tokenizer={type(parler_tokenizer)}, piper={type(piper_voice)}. Init Error: {tts_init_error}")
        
        return FileResponse(output_path, media_type="audio/wav", filename="smiley_response.wav")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@router.get("/debug")
def debug_env():
    import sys
    return {"executable": sys.executable, "path": sys.path}

# Trigger reload
