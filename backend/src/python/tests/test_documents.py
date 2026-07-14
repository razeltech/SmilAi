import pytest
from app.database.connection import get_db_connection
from app.documents.service import DocumentService, DocumentRepository

def test_document_ingestion_and_lifecycle():
    # Use seeded database values
    org_id = "cad61a6c-cb04-4d08-a103-7deeafb84837"
    subject_id = "a7f984b9-ae55-41af-ba93-0bced1614c57"
    filename = "pytest_doc.txt"
    content = "Pytest is a testing framework. It makes it easy to write simple tests."
    
    conn = get_db_connection()
    # Cleanup old run data cascade to respect FOREIGN KEY constraints
    doc_rows = conn.execute("SELECT id FROM documents WHERE name = ?", (filename,)).fetchall()
    for row in doc_rows:
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (row["id"],))
    conn.execute("DELETE FROM documents WHERE name = ?", (filename,))
    conn.commit()
    
    # 1. Test Ingestion
    res = DocumentService.ingest_parsed_document(filename, content, org_id, subject_id)
    assert res["message"] == "Success"
    doc_id = res["doc_id"]
    
    # 2. Test Get
    doc = DocumentRepository.get_by_id(conn, doc_id)
    assert doc is not None
    assert doc["name"] == filename
    assert doc["status"] == "pending"
    
    # 3. Test Patch
    success = DocumentRepository.patch_status(conn, doc_id, "approved")
    assert success is True
    doc = DocumentRepository.get_by_id(conn, doc_id)
    assert doc["status"] == "approved"
    
    # 4. Test List Active
    active_docs = DocumentRepository.list_active(conn, subject_id)
    assert any(d["id"] == doc_id for d in active_docs)
    
    # 5. Test Soft Delete
    success = DocumentRepository.soft_delete(conn, doc_id)
    assert success is True
    
    # 6. Verify Hidden after Soft Delete
    active_docs_after = DocumentRepository.list_active(conn, subject_id)
    assert not any(d["id"] == doc_id for d in active_docs_after)
    
    conn.close()
