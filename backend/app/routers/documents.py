from fastapi import APIRouter, HTTPException, status

from ..templates import ALL_DOCUMENTS, DocumentSummary, DocumentTemplate, get_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    return [
        DocumentSummary(id=document.id, name=document.name, description=document.description)
        for document in ALL_DOCUMENTS
    ]


@router.get("/{document_id}", response_model=DocumentTemplate)
def get_document_detail(document_id: str) -> DocumentTemplate:
    document = get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown document type")
    return document
