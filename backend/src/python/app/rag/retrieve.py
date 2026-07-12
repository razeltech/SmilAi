try:
    from sentence_transformers import CrossEncoder
    reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
except Exception as e:
    print(f"[SmilAI AI Fallback] Disabling CrossEncoder (Reranker) due to environment error: {e}")
    class DummyCrossEncoder:
        def predict(self, pairs):
            return [0.5 for _ in pairs]
    reranker = DummyCrossEncoder()

from rank_bm25 import BM25Okapi
import os

from ..database.vector_db import VectorDB
from ..database.connection import get_db_connection
from .ingest import embedding_model

# Ensure strict local caching
os.environ["HF_HOME"] = os.environ.get("HF_HOME", "./models/hf_cache")

def staged_hybrid_search(query: str, org_id: str, subject_id: str, top_k: int = 5):
    """
    The Staged Hybrid Retrieval Pipeline (For 500+ Students)
    1. SQL Pre-Filter: Instantly drops chunks not in this subject/org.
    2. Dense Vector Search: ChromaDB finds the top 50 semantically similar chunks.
    3. Lexical BM25 (Optional/Fallback): Used for exact keyword matches.
    4. Cross-Encoder Reranking: Re-evaluates the top 50 against the query for ultimate precision.
    """
    
    # 1. Generate query embedding
    query_embedding = embedding_model.encode([query]).tolist()[0]
    
    # 2. Vector Search with Metadata Pre-Filtering (Stage 1 & 2)
    # The 'where' clause is the equivalent of our SQL filter pushed down into Chroma.
    # It ensures we never accidentally return another school's or subject's data.
    collection = VectorDB.get_collection()
    
    vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=50, # Broad recall
        where={
            "$and": [
                {"org_id": org_id},
                {"subject_id": subject_id}
            ]
        }
    )
    
    if not vector_results['documents'] or not vector_results['documents'][0]:
        return []
        
    documents = vector_results['documents'][0]
    metadatas = vector_results['metadatas'][0]
    
    # 3. Cross-Encoder Reranking (Stage 4)
    # We pair the query with each document to get a highly accurate relevance score.
    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs)
    
    # Zip documents, metadata, and scores together, then sort by score descending
    scored_docs = list(zip(scores, documents, metadatas))
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # 4. Return the Top K precision chunks
    final_chunks = []
    for score, doc, meta in scored_docs[:top_k]:
        final_chunks.append({
            "text": doc,
            "relevance_score": float(score),
            "doc_id": meta["doc_id"]
        })
        
    return final_chunks
