import sys
import pytest
from unittest.mock import MagicMock

# Create mock modules
mock_torch = MagicMock()
mock_st = MagicMock()

mock_model_instance = MagicMock()
mock_encode_result = MagicMock()
mock_encode_result.tolist.return_value = [[0.1] * 384]
mock_model_instance.encode.return_value = mock_encode_result

mock_cross_encoder_instance = MagicMock()
mock_cross_encoder_instance.predict.return_value = [0.5] * 100
mock_st.CrossEncoder.return_value = mock_cross_encoder_instance
mock_st.SentenceTransformer.return_value = mock_model_instance

mock_chroma = MagicMock()
mock_collection = MagicMock()
mock_collection.query.return_value = {
    'documents': [['This is a sample chapter text about Quadratic Equations. It explains the quadratic formula.']],
    'metadatas': [[{'doc_id': '123', 'org_id': 'cad61a6c-cb04-4d08-a103-7deeafb84837', 'subject_id': 'a7f984b9-ae55-41af-ba93-0bced1614c57', 'chunk_index': 0}]]
}
mock_chroma.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection

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

# Now it is safe to import the app
from app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def client():
    """Returns a TestClient instance attached to the mocked FastAPI app."""
    with TestClient(app) as client:
        yield client
