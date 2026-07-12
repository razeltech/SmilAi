import sys
import types
import pytest
from unittest.mock import MagicMock

# Create mock modules
mock_torch = MagicMock()
mock_st = MagicMock()
mock_st.CrossEncoder = MagicMock

mock_model_instance = MagicMock()
mock_encode_result = MagicMock()
mock_encode_result.tolist.return_value = [0.1, 0.2, 0.3]
mock_model_instance.encode.return_value = mock_encode_result
mock_st.SentenceTransformer.return_value = mock_model_instance

mock_chroma = MagicMock()
mock_chroma.PersistentClient = MagicMock

mock_whisper = MagicMock()
mock_whisper.WhisperModel = MagicMock

# Inject mock modules into sys.modules BEFORE app is imported
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = mock_torch.nn
sys.modules['sentence_transformers'] = mock_st
sys.modules['faster_whisper'] = mock_whisper

mock_piper = MagicMock()
mock_piper.voice = MagicMock()
sys.modules['piper'] = mock_piper
sys.modules['piper.voice'] = mock_piper.voice

# Now it is safe to import the app without triggering PyTorch >= 2.4 crashes
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    """Returns a TestClient instance attached to the mocked FastAPI app."""
    with TestClient(app) as client:
        yield client
