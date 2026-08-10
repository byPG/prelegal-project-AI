import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_connection
from ..deps import get_current_user
from ..schemas import (
    SaveDocumentRequest,
    SavedDocumentResponse,
    SavedDocumentSummary,
    UpdateDocumentRequest,
    UserResponse,
)
from ..templates import get_document

router = APIRouter(prefix="/api/saved-documents", tags=["saved-documents"])


def _row_to_response(row: sqlite3.Row) -> SavedDocumentResponse:
    document = get_document(row["document_type_id"])
    return SavedDocumentResponse(
        id=row["id"],
        document_type_id=row["document_type_id"],
        document_name=document.name if document else row["document_type_id"],
        title=row["title"],
        fields=json.loads(row["fields_json"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("", response_model=SavedDocumentResponse, status_code=status.HTTP_201_CREATED)
def save_document(
    payload: SaveDocumentRequest, current_user: UserResponse = Depends(get_current_user)
) -> SavedDocumentResponse:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (user_id, document_type_id, title, fields_json)
            VALUES (?, ?, ?, ?)
            """,
            (current_user.id, payload.document_type_id, payload.title, json.dumps(payload.fields)),
        )
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (cursor.lastrowid,)).fetchone()

    return _row_to_response(row)


@router.get("", response_model=list[SavedDocumentSummary])
def list_saved_documents(current_user: UserResponse = Depends(get_current_user)) -> list[SavedDocumentSummary]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY updated_at DESC", (current_user.id,)
        ).fetchall()

    return [_row_to_response(row) for row in rows]


@router.get("/{saved_document_id}", response_model=SavedDocumentResponse)
def get_saved_document(
    saved_document_id: int, current_user: UserResponse = Depends(get_current_user)
) -> SavedDocumentResponse:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ? AND user_id = ?", (saved_document_id, current_user.id)
        ).fetchone()

    if row is None:
        # 404, not 403 — don't confirm to the caller that a document with
        # this id exists at all if it isn't theirs.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    return _row_to_response(row)


@router.put("/{saved_document_id}", response_model=SavedDocumentResponse)
def update_saved_document(
    saved_document_id: int,
    payload: UpdateDocumentRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> SavedDocumentResponse:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE documents
            SET title = ?, fields_json = ?, updated_at = datetime('now')
            WHERE id = ? AND user_id = ?
            """,
            (payload.title, json.dumps(payload.fields), saved_document_id, current_user.id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (saved_document_id,)).fetchone()

    return _row_to_response(row)


@router.delete("/{saved_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_document(
    saved_document_id: int, current_user: UserResponse = Depends(get_current_user)
) -> None:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM documents WHERE id = ? AND user_id = ?", (saved_document_id, current_user.id)
        )
    if cursor.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
