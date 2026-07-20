import os
import uuid
import wave
import io
import urllib.request
import asyncio
import logging
import re
import hashlib
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

# Strictly enforce offline local caching for AI models
os.environ["HF_HOME"] = os.environ.get("HF_HOME", "./models/hf_cache")
PIPER_CACHE_DIR = os.path.join(os.environ["HF_HOME"], "piper")
os.makedirs(PIPER_CACHE_DIR, exist_ok=True)

PIPER_VOICE_NAME = "en_US-lessac-medium"
PIPER_ONNX_URL = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/{PIPER_VOICE_NAME}.onnx"
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
    from ..core.config import active_profile
    if whisper_model is None:
        logger.info(f"Booting up Local Whisper STT Engine ({active_profile.whisper_model})...")
        try:
            from faster_whisper import WhisperModel
            # STT stays on CPU to keep VRAM free for LLM/Parler
            whisper_model = WhisperModel(active_profile.whisper_model, device="cpu", compute_type="int8")
        except ImportError:
            logger.error("faster_whisper is not installed.")
            raise RuntimeError("faster_whisper is not installed. Voice STT unavailable.")
    return whisper_model

def initialize_tts_engine():
    import sys
    logger.error(f"UVICORN WORKER EXEC: {sys.executable}")
    logger.error(f"UVICORN WORKER PATH: {sys.path}")
    global parler_model, parler_tokenizer, piper_voice, tts_engine_initialized, tts_init_error
    from ..core.config import active_profile
    
    if tts_engine_initialized and (parler_model is not None or piper_voice is not None):
        return
    
    logger.info("Booting up Two-Tier TTS Engine...")
    
    # 1. Try Loading Parler-TTS (Indian Accent) on GPU if enabled in profile
    if active_profile.tts_engine == "parler":
        try:
            import torch
            if torch.cuda.is_available():
                free_mem, _ = torch.cuda.mem_get_info()
                if free_mem > 2 * 1024 * 1024 * 1024:
                    from parler_tts import ParlerTTSForConditionalGeneration
                    from transformers import AutoTokenizer
                    logger.info("GPU detected with >2GB VRAM. Loading ai4bharat/indic-parler-tts locally (will download if missing)...")
                    # Set local_files_only=False to allow initial download for the RTX 3060
                    parler_model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts", local_files_only=False).to("cuda")
                    parler_tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts", local_files_only=False)
                    logger.info("Indic Parler-TTS loaded successfully on GPU.")
                else:
                    logger.warning(f"Not enough VRAM for Parler-TTS (Free: {free_mem/(1024**3):.2f}GB). Falling back to Piper.")
            else:
                logger.warning("No GPU detected for Parler-TTS. Skipping to fallback.")
        except OSError: 
            logger.warning("Parler-TTS models failed to load or download.")
            parler_model = None
            parler_tokenizer = None
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
            
            if not os.path.exists(onnx_path) or not os.path.exists(json_path):
                logger.warning(f"Piper models not found at {PIPER_CACHE_DIR}. Disabling Voice capabilities.")
            else:
                piper_voice = PiperVoice.load(onnx_path, config_path=json_path)
                logger.info("Piper TTS Fallback loaded successfully.")
        except Exception as e:
            import traceback
            import sys
            tts_init_error = f"Piper error: {traceback.format_exc()} EXEC: {sys.executable}"
            logger.error(f"Piper TTS Fallback unavailable ({e}).")
        
    tts_engine_initialized = True
    
    # Register global capabilities
    from ..core.capabilities import capabilities
    if parler_model is None and piper_voice is None:
        capabilities.voice = False
    else:
        capabilities.voice = True

def require_voice_capability():
    from ..core.capabilities import capabilities
    if not capabilities.voice:
        raise HTTPException(status_code=503, detail="Voice subsystem is disabled or missing models.")

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    require_voice_capability()
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

VOICE_PROMPT_VERSION = "2026_07_v2"

# A unified teacher voice with different speaking styles
CORE_TEACHER_PERSONA = "A warm Indian female voice speaking clear Indian English. She sounds like an experienced school teacher who is encouraging and reassuring."

SPEAKING_STYLES = {
    "warm": f"{CORE_TEACHER_PERSONA} She speaks slowly with gentle pauses, sounding like she is smiling gently while speaking. Her voice is calm, reassuring, expressive, and natural.",
    "focused": f"{CORE_TEACHER_PERSONA} She speaks confidently and at an unhurried, moderate pace. She emphasizes key educational concepts clearly and maintains a focused delivery rhythm with minimal emotional variance.",
    "comfort": f"{CORE_TEACHER_PERSONA} She speaks softly and slowly, reassuring the student through calm, patient pacing and slightly longer, quiet pauses. She never sounds rushed or worried.",
    "quiz": f"{CORE_TEACHER_PERSONA} She speaks clearly and enthusiastically, raising her intonation dynamically on questions and sounding excited and encouraging.",
    "story": f"{CORE_TEACHER_PERSONA} She narrates like an experienced primary school teacher reading to children, varying her pitch naturally and creating suspense with natural pauses."
}

def prepare_speech_text(text: str) -> str:
    """
    Cleans raw LLM response text before sending it to the TTS engine.
    Removes Markdown, citations, and math markers to prevent robotic reading.
    Preserves emotional punctuation, and translates list items/bullets.
    """
    # 1. Convert lists and bullets to natural transition words line-by-line
    lines = text.splitlines()
    
    # Pre-count lists and bullets to find final boundaries
    bullets = re.findall(r'^([•\-*])\s+', text, re.MULTILINE)
    total_bullets = len(bullets)
    list_matches = re.findall(r'^(\d+)\.\s+', text, re.MULTILINE)
    total_lists = len(list_matches)
    
    processed_lines = []
    bullet_index = 0
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            processed_lines.append("")
            continue
            
        # Check for numbered lists: e.g. "1. " or "2. "
        num_match = re.match(r'^(\d+)\.\s+(.*)', line_str)
        if num_match:
            num = int(num_match.group(1))
            content = num_match.group(2)
            
            markers = {
                1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth",
                6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth"
            }
            if num == total_lists and total_lists > 1:
                marker = "Finally"
            else:
                marker = markers.get(num, "Next")
            processed_lines.append(f"{marker}, {content}")
            continue
            
        # Check for bullets: •, -, *
        bullet_match = re.match(r'^([•\-*])\s+(.*)', line_str)
        if bullet_match:
            content = bullet_match.group(2)
            bullet_index += 1
            if bullet_index == 1:
                marker = "First"
            elif bullet_index == total_bullets and total_bullets > 1:
                marker = "Finally"
            else:
                marker = "Also"
            processed_lines.append(f"{marker}, {content}")
            continue
            
        processed_lines.append(line_str)
        
    cleaned = "\n".join(processed_lines)
    
    # 2. Remove inline brackets citations like [1] or [2]
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    
    # 3. Remove LaTeX math wrappers: $$...$$ or $...$ or \(...\) or \[...\]
    cleaned = re.sub(r'\$\$', '', cleaned)
    cleaned = re.sub(r'\$', '', cleaned)
    cleaned = re.sub(r'\\\(', '', cleaned)
    cleaned = re.sub(r'\\\)', '', cleaned)
    cleaned = re.sub(r'\\\[', '', cleaned)
    cleaned = re.sub(r'\\\]', '', cleaned)
    
    # 4. Remove markdown formatting like * or ** or # or `
    cleaned = re.sub(r'[*_`#]', '', cleaned)
    
    # 5. Remove leading/trailing spaces and collapse multiple whitespaces/newlines
    cleaned = re.sub(r'[ \t]+', ' ', cleaned).strip()
    cleaned = re.sub(r'\n+', ' ', cleaned).strip()
    return cleaned

def classify_voice_style(student_message: str, assistant_response: str) -> str:
    """
    Dynamically classifies speaking style based on user query and teacher response context.
    """
    user_lower = student_message.lower()
    assistant_lower = assistant_response.lower()
    
    # 1. Comfort Mode
    comfort_keywords = {"scared", "afraid", "worry", "worried", "calm", "relax", "nervous", "anxious", "fail", "stress", "stressed", "difficult"}
    comfort_assistant_keywords = {"don't worry", "take a deep breath", "calm", "gentle", "reassure", "it is okay"}
    if (any(w in user_lower for w in comfort_keywords) or 
        any(w in assistant_lower for w in comfort_assistant_keywords)):
        return "comfort"
        
    # 2. Quiz Mode
    quiz_keywords = {"quiz", "test", "ask me", "question", "exercise"}
    quiz_assistant_keywords = {"let's practice", "here is a question", "multiple choice", "quiz", "what is the"}
    if (any(w in user_lower for w in quiz_keywords) or 
        any(w in assistant_lower for w in quiz_assistant_keywords)):
        return "quiz"
        
    # 3. Story Mode
    story_keywords = {"story", "tale", "imagine", "once upon"}
    story_assistant_keywords = {"once upon a time", "let's imagine", "here is a story"}
    if (any(w in user_lower for w in story_keywords) or 
        any(w in assistant_lower for w in story_assistant_keywords)):
        return "story"
        
    # 4. Focused Mode
    focused_keywords = {"revision", "revise", "quick", "summary", "exam", "board", "syllabus", "fast", "recap"}
    if any(w in user_lower for w in focused_keywords):
        return "focused"
        
    return "warm"

def split_into_sentences(text: str) -> list:
    """
    Splits text into separate sentences for chunked TTS generation.
    """
    sentence_end = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_end.split(text.strip())
    return [s.strip() for s in sentences if s.strip()]

def stitch_wav_files(input_paths: list, output_path: str):
    """
    Stitches multiple WAV files together using python's wave module.
    """
    if not input_paths:
        return
    with wave.open(input_paths[0], 'rb') as first_wav:
        params = first_wav.getparams()
        
    with wave.open(output_path, 'wb') as stitched_wav:
        stitched_wav.setparams(params)
        for path in input_paths:
            with wave.open(path, 'rb') as src_wav:
                stitched_wav.writeframes(src_wav.readframes(src_wav.getnframes()))

@router.post("/speak")
def generate_speech(text: str, user_message: str = "", voice_style: str = "auto"):
    """
    Takes Smiley's text response and generates a beautiful Indian-accented voice using Parler-TTS.
    Falls back to Piper TTS if Parler is unavailable. Returns a WAV audio file.
    Supports dynamic speaking styles, sentence segmentation caching, and WAV stitching.
    """
    require_voice_capability()
    initialize_tts_engine()
    
    # 1. Clean the text using the Speech Preparation Layer
    cleaned_text = prepare_speech_text(text)
    if not cleaned_text:
        cleaned_text = "I am checking that for you."

    # 2. Dynamic speaking style selection
    style = voice_style
    if style == "auto":
        style = classify_voice_style(user_message, text)
    if style not in SPEAKING_STYLES:
        style = "warm"

    # 3. Compute final stitched WAV cache path
    total_hash = hashlib.sha256(f"{cleaned_text}_{style}_{VOICE_PROMPT_VERSION}".encode("utf-8")).hexdigest()
    os.makedirs("./database/temp_audio", exist_ok=True)
    final_output_path = f"./database/temp_audio/{total_hash}.wav"
    
    # Return immediately if cached version exists
    if os.path.exists(final_output_path):
        return FileResponse(final_output_path, media_type="audio/wav", filename="smiley_response.wav")
        
    # 4. Segment text into sentences for low latency caching & synthesis stability
    sentences = split_into_sentences(cleaned_text)
    if not sentences:
        sentences = [cleaned_text]
        
    sentence_clips = []
    os.makedirs("./database/temp_audio/sentences", exist_ok=True)
    
    try:
        for sentence in sentences:
            sentence_hash = hashlib.sha256(f"{sentence}_{style}_{VOICE_PROMPT_VERSION}".encode("utf-8")).hexdigest()
            clip_path = f"./database/temp_audio/sentences/{sentence_hash}.wav"
            
            # If sentence clip is already cached, reuse it
            if not os.path.exists(clip_path):
                if parler_model and parler_tokenizer:
                    # Tier 1: Parler-TTS Indian Teacher Voice
                    import soundfile as sf
                    description = SPEAKING_STYLES[style]
                    
                    input_ids = parler_tokenizer(description, return_tensors="pt").input_ids.to("cuda")
                    prompt_input_ids = parler_tokenizer(sentence, return_tensors="pt").input_ids.to("cuda")
                    
                    generation = parler_model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
                    audio_arr = generation.cpu().numpy().squeeze()
                    
                    sf.write(clip_path, audio_arr, parler_model.config.sampling_rate, format='wav')
                elif piper_voice:
                    # Tier 2: Piper Fallback with Lessac voice
                    with wave.open(clip_path, "wb") as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2) # 16-bit PCM
                        wav_file.setframerate(piper_voice.config.sample_rate)
                        piper_voice.synthesize_wav(sentence, wav_file)
                else:
                    raise RuntimeError(f"No TTS voice model is initialized. Init error: {tts_init_error}")
            
            sentence_clips.append(clip_path)
            
        # 5. Stitch all WAV files together
        stitch_wav_files(sentence_clips, final_output_path)
        return FileResponse(final_output_path, media_type="audio/wav", filename="smiley_response.wav")
        
    except Exception as e:
        logger.exception("Failed to generate voice speech")
        if os.path.exists(final_output_path):
            try:
                os.remove(final_output_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@router.get("/debug")
def debug_env():
    import sys
    return {"executable": sys.executable, "path": sys.path}

# Trigger reload
