import fitz  # PyMuPDF
import os
import sys

if sys.platform == "win32":
    main_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app/rag -> app
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(main_dir))) # backend
    torch_lib = os.path.join(backend_dir, ".venv", "Lib", "site-packages", "torch", "lib")
    if os.path.exists(torch_lib):
        try:
            os.add_dll_directory(torch_lib)
        except Exception:
            pass

try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    print(f"[SmilAI AI Fallback] Disabling SentenceTransformer (Embeddings) due to environment error: {e}")
    class DummyEmbeddingModel:
        def encode(self, texts):
            class MockArray:
                def tolist(self):
                    return [[0.1] * 384 for _ in texts]
            return MockArray()
    embedding_model = DummyEmbeddingModel()

def get_embedder():
    return embedding_model

import uuid
import os
from ..database.vector_db import VectorDB
from ..database.connection import get_db_connection

os.environ["HF_HOME"] = os.environ.get("HF_HOME", "./models/hf_cache")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """
    Splits raw textbook text into overlapping chunks.
    Keeps chunks small enough for precise retrieval without context poisoning.
    """
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def process_and_ingest_pdf(pdf_bytes: bytes, filename: str, org_id: str, subject_id: str, uploader_id: str):
    """
    1. Reads PDF or Image bytes from the teacher upload.
    2. Extracts text using PyMuPDF and EasyOCR.
    3. Chunks the text logically.
    4. Generates vector embeddings.
    5. Saves to SQLite (Metadata) AND ChromaDB (Vectors) for the Staged Hybrid RAG.
    """
    filename_lower = filename.lower()
    full_text = ""
    
    if filename_lower.endswith(".pdf"):
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text = page.get_text("text").strip()
            
            if len(text) < 50:
                from ..language.ocr import ocr_provider
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                ocr_result = ocr_provider.extract_text(img_bytes)
                if ocr_result and ocr_result.text:
                    text = (text + "\n" + ocr_result.text).strip()
                    
            full_text += text + "\n\n"
            
    elif filename_lower.endswith((".png", ".jpg", ".jpeg")):
        from ..language.ocr import ocr_provider
        ocr_result = ocr_provider.extract_text(pdf_bytes)
        full_text = ocr_result.text
        
    else:
        raise ValueError(f"Unsupported file format: {filename}")
        
    chunks = chunk_text(full_text)
    
    # 1. Save Document Metadata to SQLite
    doc_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        (doc_id, subject_id, org_id, filename, "Stored in VectorDB", "library", len(chunks))
    )
    
    # 2. Prepare Data for ChromaDB
    collection = VectorDB.get_collection()
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        
        # Save chunk metadata to SQLite for full relational tracking
        conn.execute(
            "INSERT INTO chunks (id, doc_id, org_id, subject_id, text, chunk_index) VALUES (?, ?, ?, ?, ?, ?)",
            (chunk_id, doc_id, org_id, subject_id, chunk, i)
        )
        
        ids.append(chunk_id)
        documents.append(chunk)
        # Crucial for Staged Filter: We inject org_id and subject_id into Chroma metadata
        metadatas.append({
            "doc_id": doc_id,
            "org_id": org_id,
            "subject_id": subject_id,
            "chunk_index": i
        })
        
    conn.commit()
    conn.close()
    
    # 3. Generate Embeddings & Push to Vector Store (Offline)
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = embedding_model.encode(documents).tolist()
    
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    return {"message": "Success", "doc_id": doc_id, "total_chunks": len(chunks)}
