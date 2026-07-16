from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlite3 import Connection
from pydantic import BaseModel

from ...database.connection import get_db
from ...documents.service import DocumentRepository

router = APIRouter(tags=["Admin - Documents"])

class DocumentPatch(BaseModel):
    status: str

@router.get("/subjects/{subjectId}/documents")
def get_subject_documents(subjectId: str, db: Connection = Depends(get_db)):
    """Returns all active uploaded documents for a subject."""
    rows = DocumentRepository.list_active(db, subjectId)
    return [
        {
            "id": r["id"],
            "subjectId": r["subject_id"],
            "orgId": r["org_id"],
            "name": r["name"],
            "type": r["type"],
            "chunkCount": r["chunk_count"],
            "uploadedAt": r["uploaded_at"],
            "status": r.get("status", "approved")
        }
        for r in rows
    ]

@router.post("/subjects/{subjectId}/documents/upload")
async def upload_subject_document(subjectId: str, file: UploadFile = File(...), db: Connection = Depends(get_db)):
    """Transactionally ingests an uploaded document (PDF/DOCX/TXT) for a subject."""
    subject = db.execute("SELECT org_id FROM subjects WHERE id = ?", (subjectId,)).fetchone()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    org_id = subject["org_id"]
    
    from ...documents.ingestion import process_document_upload
    res = await process_document_upload(file, org_id, subjectId)
            
    return {
        "processedCount": 1,
        "totalChunks": res["total_chunks"],
        "documents": [
            {
                "id": res["doc_id"],
                "name": file.filename,
                "status": "pending"
            }
        ]
    }

@router.patch("/documents/{id}")
def patch_document(id: str, req: DocumentPatch, db: Connection = Depends(get_db)):
    """Updates a document's status (approved, archived, pending)."""
    success = DocumentRepository.patch_status(db, id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success", "status": req.status}

@router.post("/documents/{id}/approve")
def approve_document(id: str, db: Connection = Depends(get_db)):
    """Convenience endpoint specifically called by frontend to approve document."""
    success = DocumentRepository.patch_status(db, id, "approved")
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success", "status": "approved"}

@router.delete("/documents/{id}")
def delete_document(id: str, db: Connection = Depends(get_db)):
    """Soft deletes a document by setting status = 'archived'."""
    success = DocumentRepository.soft_delete(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Success"}
