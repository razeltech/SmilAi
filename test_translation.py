import sys
import os

# Add backend python path so we can import app modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'src', 'python')))

from app.language.indictrans2 import translation_provider

def print_result(name: str, res):
    print(f"\n--- {name} ---")
    print(f"Success:   {res.success}")
    if not res.success:
        print(f"Error:     {res.error}")
    print(f"Direction: {res.direction}")
    print(f"Model:     {res.model_name}")
    print(f"Latency:   {res.latency_ms:.2f} ms")
    print(f"Source:    {res.source_language}")
    print(f"Target:    {res.target_language}")
    print(f"Result:\n{res.translated_text}")

def run_tests():
    print("Testing TranslationProvider Initialization and Inference...")
    
    # Check initial health
    print("Initial Health:", translation_provider.health())

    # 1. Empty String
    res_empty = translation_provider.translate("", "en", "te")
    print_result("Test 1: Empty String", res_empty)

    # 2. Basic en -> te
    print("\nLoading en-indic model and executing first translation (may take time to download)...")
    res_en_te = translation_provider.translate("Hello, how are you?", "en", "te")
    print_result("Test 2: Basic EN -> TE", res_en_te)
    print("Health after en-indic:", translation_provider.health())

    # 3. Basic te -> en (Should trigger swap)
    print("\nLoading indic-en model (SWAP) and executing translation...")
    res_te_en = translation_provider.translate("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "en")
    print_result("Test 3: Basic TE -> EN", res_te_en)
    print("Health after indic-en:", translation_provider.health())
    
    # 4. Large Paragraph en -> te
    large_text = (
        "Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy "
        "that, through cellular respiration, can later be released to fuel the organism's activities. "
        "Some of this chemical energy is stored in carbohydrate molecules, such as sugars and starches, "
        "which are synthesized from carbon dioxide and water."
    )
    res_large = translation_provider.translate(large_text, "en", "te")
    print_result("Test 4: Large Paragraph EN -> TE", res_large)

    # 5. Mixed Content (Medical/Educational) en -> te
    mixed_content = (
        "The heart pumps blood through four chambers. "
        "LV = Left Ventricle. "
        "Normal BP is 120/80."
    )
    res_mixed = translation_provider.translate(mixed_content, "en", "te")
    print_result("Test 5: Mixed Content EN -> TE", res_mixed)

    # 6. Invalid pair
    res_invalid = translation_provider.translate("Bonjour", "fr", "en")
    print_result("Test 6: Invalid Language Pair", res_invalid)

if __name__ == "__main__":
    run_tests()
