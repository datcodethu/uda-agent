import tempfile
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import verify_key
from app.pipeline import index_service
from app.pipeline.preprocessor.pdf_loader import load_text
from app.pipeline.retrieval import chunk_store
from app.schemas.ingest_schema import DocumentInfo, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"], dependencies=[Depends(verify_key)])


@router.post("", response_model=IngestResponse)
def ingest(file: UploadFile = File(...), doc_name: str = Form(...), status: str = Form("ACTIVE")):
    if status not in ("ACTIVE", "EXPIRED"):
        raise HTTPException(400, "status phải là 'ACTIVE' hoặc 'EXPIRED'")
    suffix = Path(file.filename or "").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        text = load_text(tmp_path)
        return index_service.index_document(doc_name, text, status)
    except ValueError as e:
        raise HTTPException(422, str(e))
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents():
    return chunk_store.list_documents()


@router.delete("/documents/{doc_name}")
def delete_document(doc_name: str):
    return index_service.remove_document(doc_name)
