import os
import sys
from huggingface_hub import snapshot_download

def download_offline_models():
    print("=== SmilAI Offline Model Installer ===")
    print("This script downloads the IndicTrans2 models for 100% offline usage.")
    print("Ensure you have run 'huggingface-cli login' and accepted the AI4Bharat license first!\n")
    
    # Target directory: backend/models/indictrans2/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'models', 'indictrans2'))
    os.makedirs(base_dir, exist_ok=True)
    
    models = {
        "en-indic": "ai4bharat/indictrans2-en-indic-1B",
        "indic-en": "ai4bharat/indictrans2-indic-en-1B"
    }
    
    for direction, repo_id in models.items():
        target_path = os.path.join(base_dir, direction)
        print(f"\nDownloading {repo_id} to {target_path}...")
        try:
            # snapshot_download downloads the entire repo to a local directory
            snapshot_download(
                repo_id=repo_id, 
                local_dir=target_path,
                local_dir_use_symlinks=False, # Important for Windows portability
                ignore_patterns=["*.msgpack", "*.h5", "*.ot"] # Ignore non-safetensors/pytorch bins if possible, but keeping it simple
            )
            print(f"✅ Successfully downloaded {direction} model.")
        except Exception as e:
            print(f"❌ Failed to download {direction}. Error: {e}")
            print("\nDid you forget to authenticate? Run: huggingface-cli login")
            sys.exit(1)
            
    print("\n🎉 All models downloaded successfully!")
    print("SmilAI will now load these models completely offline without contacting Hugging Face.")

if __name__ == "__main__":
    download_offline_models()
