from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..rag.ingest import process_and_ingest_pdf

router = APIRouter(prefix="/content", tags=["Content Management"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    org_id: str = Form(...),
    subject_id: str = Form(...),
    uploader_id: str = Form(...)
):
    """
    Teacher 'Library Mode' upload endpoint.
    Takes a PDF curriculum file and securely ingests it into the Staged Hybrid RAG system.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for ingestion.")
    
    try:
        pdf_bytes = await file.read()
        result = process_and_ingest_pdf(
            pdf_bytes=pdf_bytes,
            filename=file.filename,
            org_id=org_id,
            subject_id=subject_id,
            uploader_id=uploader_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")
