from pydantic import BaseModel


class IngestResponse(BaseModel):
    doc_name: str
    chunks: int
    status: str


class DocumentInfo(BaseModel):
    doc_name: str
    status: str
    chunks: int
