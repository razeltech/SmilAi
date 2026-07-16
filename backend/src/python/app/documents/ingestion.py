import logging
import uuid
import re
from fastapi import UploadFile, HTTPException

from ..database.connection import get_db_connection
from ..database.vector_db import VectorDB
from ..core.config import active_profile

logger = logging.getLogger(__name__)

def semantic_chunking(text: str) -> list[str]:
    """
    Implements a hierarchy: Heading -> Section -> Paragraph -> Sentence Overlap.
    Currently uses simple paragraph splitting with max_chunk_size limit.
    """
    max_chunk_size = active_profile.max_chunk_size
    
    # Simple semantic splitting by double newlines (paragraphs/sections)
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
            
        # If adding this paragraph exceeds max chunk size, push the current chunk
        # (Using a very basic character count heuristic for "tokens" for now)
        if len(current_chunk) + len(p) > max_chunk_size * 4: # approx 4 chars per token
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p
        else:
            if current_chunk:
                current_chunk += "\n\n" + p
            else:
                current_chunk = p
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

async def extract_text_from_upload(file: UploadFile) -> str:
    """Extracts raw text based on file extension."""
    filename = file.filename.lower()
    content_bytes = await file.read()
    
    if filename.endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            text = "\n\n".join(page.get_text("text") for page in doc)
            return text
        except ImportError:
            raise HTTPException(status_code=500, detail="PyMuPDF (fitz) is not installed.")
            
    elif filename.endswith(".docx"):
        try:
            import docx
            from io import BytesIO
            doc = docx.Document(BytesIO(content_bytes))
            text = "\n\n".join(paragraph.text for paragraph in doc.paragraphs)
            return text
        except ImportError:
            raise HTTPException(status_code=500, detail="python-docx is not installed.")
            
    elif filename.endswith(".txt") or filename.endswith(".md"):
        return content_bytes.decode("utf-8", errors="replace")
        
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, TXT, or MD.")

async def process_document_upload(file: UploadFile, org_id: str, subject_id: str) -> dict:
    """
    The full advanced ingestion pipeline:
    Upload -> Extract -> Semantic Chunk -> Embed -> SQLite -> ChromaDB
    """
    # 1. Extraction
    text = await extract_text_from_upload(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Uploaded document contains no readable text.")
        
    # 2. Semantic Chunking
    chunks = semantic_chunking(text)
    
    if len(chunks) == 0:
        raise HTTPException(status_code=400, detail="Failed to extract any logical chunks.")
        
    # 3. Transactional Save (SQLite & Chroma)
    doc_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("BEGIN TRANSACTION;")
    
    ids = []
    documents = []
    metadatas = []
    
    try:
        cursor.execute(
            "INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)",
            (doc_id, subject_id, org_id, file.filename, "Stored in VectorDB", "library", len(chunks), "pending")
        )
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            cursor.execute(
                "INSERT INTO chunks (id, doc_id, org_id, subject_id, text, chunk_index) VALUES (?, ?, ?, ?, ?, ?)",
                (chunk_id, doc_id, org_id, subject_id, chunk, i)
            )
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "doc_id": doc_id,
                "org_id": org_id,
                "subject_id": subject_id,
                "chunk_index": i
            })
            
        # Get embedder directly avoiding circular import on boot
        from ..rag.ingest import get_embedder
        embedding_model = get_embedder()
        
        collection = VectorDB.get_collection()
        embeddings = embedding_model.encode(documents).tolist()
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        conn.commit()
        return {"message": "Success", "doc_id": doc_id, "total_chunks": len(chunks)}
        
    except Exception as e:
        logger.error(f"Transaction failed. Rolling back database and vector stores: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            collection = VectorDB.get_collection()
            collection.delete(ids=ids)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")
    finally:
        conn.close()
