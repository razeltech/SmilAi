import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel
from piper.voice import PiperVoice
import uuid
import wave

# Strictly enforce offline local caching for Whisper models
os.environ["HF_HOME"] = os.environ.get("HF_HOME", "./models/hf_cache")

router = APIRouter(prefix="/voice", tags=["Voice Engine"])

# Load Whisper model globally to avoid bootup latency on every request
# 'base.en' is lightning fast on CPU/GPU and perfectly accurate for 1st graders
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Booting up Local Whisper STT Engine...")
        # device="cuda" if RTX 3060 is fully available, else "cpu". 
        # Using "auto" allows it to fallback safely without crashing.
        whisper_model = WhisperModel("base.en", device="auto", compute_type="default")
    return whisper_model

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Takes an audio file from the 1st grader (e.g. WebM or WAV from frontend)
    and converts it instantly to text using the local Whisper model.
    No data goes to the cloud.
    """
    # Save uploaded file to temporary cache
    os.makedirs("./database/temp_audio", exist_ok=True)
    temp_audio_path = f"./database/temp_audio/{uuid.uuid4()}_{file.filename}"
    
    try:
        with open(temp_audio_path, "wb") as f:
            f.write(await file.read())
            
        model = get_whisper_model()
        segments, info = model.transcribe(temp_audio_path, beam_size=5)
        
        text = " ".join([segment.text for segment in segments])
        
        return {"text": text.strip(), "language": info.language}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice Recognition Error: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@router.post("/speak")
async def generate_speech(text: str):
    """
    Takes Smiley's text response and generates a beautiful, motherly voice
    using Piper TTS locally. Returns a WAV audio file.
    """
    # Piper TTS logic will go here.
    # We will generate a wav file and return it via FileResponse.
    # Note: If piper-tts fails to install cleanly on Windows, we will spawn the standalone Piper binary.
    
    os.makedirs("./database/temp_audio", exist_ok=True)
    output_path = f"./database/temp_audio/{uuid.uuid4()}_smiley.wav"
    
    # Piper requires a local .onnx voice model. 
    # For Smiley, we recommend 'en_US-lessac-medium.onnx' (a gentle female voice).
    # The school admin drops this into the models directory.
    voice_model_path = os.path.join(os.environ["HF_HOME"], "piper", "en_US-lessac-medium.onnx")
    
    try:
        if os.path.exists(voice_model_path):
            # 1. Real Piper TTS Execution
            voice = PiperVoice.load(voice_model_path)
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(text, wav_file)
        else:
            # 2. Fallback: If model isn't downloaded yet, use pyttsx3 so it doesn't crash
            import pyttsx3
            print(f"Warning: Piper model not found at {voice_model_path}. Falling back to pyttsx3.")
            engine = pyttsx3.init()
            engine.save_to_file(text, output_path)
            engine.runAndWait()
        
        return FileResponse(output_path, media_type="audio/wav", filename="smiley_response.wav")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")
