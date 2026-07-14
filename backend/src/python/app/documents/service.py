import uuid
import logging
from sqlite3 import Connection

from ..database.connection import get_db_connection
from ..database.vector_db import VectorDB
from ..rag.ingest import chunk_text, embedding_model

logger = logging.getLogger(__name__)

class DocumentRepository:
    @staticmethod
    def list_active(db: Connection, subject_id: str) -> list[dict]:
        """Returns all documents for a subject that are not archived."""
        rows = db.execute(
            "SELECT * FROM documents WHERE subject_id = ? AND status != 'archived' ORDER BY uploaded_at DESC",
            (subject_id,)
        ).fetchall()
        return rows

    @staticmethod
    def get_by_id(db: Connection, doc_id: str) -> dict:
        """Retrieves a document record by its ID."""
        row = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return row

    @staticmethod
    def soft_delete(db: Connection, doc_id: str) -> bool:
        """Sets status = 'archived' to soft delete a document."""
        cursor = db.execute(
            "UPDATE documents SET status = 'archived' WHERE id = ?",
            (doc_id,)
        )
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def patch_status(db: Connection, doc_id: str, status: str) -> bool:
        """Updates a document's status (approved, pending, archived)."""
        cursor = db.execute(
            "UPDATE documents SET status = ? WHERE id = ?",
            (status, doc_id)
        )
        db.commit()
        return cursor.rowcount > 0

class DocumentService:
    @staticmethod
    def ingest_parsed_document(filename: str, content: str, org_id: str, subject_id: str) -> dict:
        """
        Ingests a pre-parsed text document:
        1. Chunks text logically.
        2. SQLite metadata mapping (documents & chunks tables) under transaction.
        3. Pushes vector chunks to ChromaDB.
        4. Commit transaction on success, or Rollback SQLite & Compensate ChromaDB on failure.
        """
        chunks = chunk_text(content)
        doc_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")
        
        ids = []
        documents = []
        metadatas = []
        
        try:
            # 1. Insert SQLite document record (defaults to pending for manual or auto review)
            cursor.execute(
                "INSERT INTO documents (id, subject_id, org_id, name, content, type, chunk_count, uploaded_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)",
                (doc_id, subject_id, org_id, filename, "Stored in VectorDB", "library", len(chunks), "pending")
            )
            
            # 2. Insert SQLite chunks mapping
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
            
            # 3. Generate embeddings & push to ChromaDB
            collection = VectorDB.get_collection()
            embeddings = embedding_model.encode(documents).tolist()
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            # 4. Commit SQLite metadata transaction
            conn.commit()
            return {"message": "Success", "doc_id": doc_id, "total_chunks": len(chunks)}
            
        except Exception as e:
            # 5. Compensatory rollback
            logger.error(f"Transaction failed. Rolling back database and vector stores: {e}")
            try:
                conn.rollback()
            except Exception as se:
                logger.error(f"SQLite rollback failed: {se}")
            try:
                collection = VectorDB.get_collection()
                # Clean up vectors if added
                collection.delete(ids=ids)
            except Exception as ve:
                logger.error(f"Compensatory vector deletion failed: {ve}")
            raise e
        finally:
            conn.close()
