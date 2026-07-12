import chromadb
from chromadb.config import Settings
import os

# Ensure the database stays strictly local, never reaching out to cloud telemetry.
CHROMA_PATH = os.environ.get("CHROMA_DB_PATH", "./database/chroma_storage")

class VectorDB:
    _instance = None

    @classmethod
    def get_client(cls):
        """Returns a singleton instance of the persistent local ChromaDB client."""
        if cls._instance is None:
            os.makedirs(CHROMA_PATH, exist_ok=True)
            cls._instance = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
        return cls._instance

    @classmethod
    def get_collection(cls, collection_name: str = "smilai_curriculum"):
        """Gets or creates the main vector collection."""
        client = cls.get_client()
        # Using default cosine similarity for robust semantic search
        return client.get_or_create_collection(
            name=collection_name, 
            metadata={"hnsw:space": "cosine"}
        )
