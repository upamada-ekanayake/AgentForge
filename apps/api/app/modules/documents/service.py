import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ROOT_DIR, settings
from app.models.enums import DocumentStatus
from app.modules.documents.models import Document, DocumentChunk
from app.modules.users.models import User
from app.modules.workspaces.service import ensure_workspace_access
from app.services.embedding_service import EmbeddingError, embed_text, embed_texts
from app.services.document_parser import DocumentParsingError, extract_text
from app.services.qdrant_service import (
    QdrantServiceError,
    search_document_chunks,
    upsert_chunk_vectors,
)
from app.services.text_chunker import chunk_text


MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
CHUNK_SIZE_BYTES = 1024 * 1024


def _safe_filename(filename: str) -> str:
    stem = Path(filename).stem.strip() or "document"
    suffix = Path(filename).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-")
    return f"{safe_stem or 'document'}{suffix}"


def _validate_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, DOCX, and TXT files are supported.",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is not supported.",
        )

    return extension


async def upload_document(
    session: AsyncSession,
    file: UploadFile,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Document:
    _validate_upload(file)
    await ensure_workspace_access(session, workspace_id, user_id)

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document user not found.",
        )

    storage_dir = settings.document_storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = _safe_filename(file.filename or "document")
    stored_filename = f"{uuid.uuid4()}-{safe_filename}"
    storage_path = storage_dir / stored_filename
    size_bytes = 0

    try:
        with storage_path.open("wb") as destination:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                size_bytes += len(chunk)
                if size_bytes > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size must be 10 MB or less.",
                    )
                destination.write(chunk)
    except Exception:
        storage_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    document = Document(
        workspace_id=workspace_id,
        user_id=user_id,
        filename=file.filename,
        content_type=file.content_type,
        storage_path=str(storage_path.relative_to(ROOT_DIR)),
        size_bytes=size_bytes,
        status=DocumentStatus.UPLOADED,
    )
    session.add(document)

    try:
        await session.flush()
        text = extract_text(storage_path)
        chunks = chunk_text(text)
        if not chunks:
            raise DocumentParsingError("No readable text was found in the document.")

        for index, chunk in enumerate(chunks):
            session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    token_count=None,
                    qdrant_point_id=None,
                ),
            )

        document.status = DocumentStatus.READY
        await session.commit()
    except DocumentParsingError:
        document.status = DocumentStatus.FAILED
        await session.commit()
    except Exception:
        await session.rollback()
        storage_path.unlink(missing_ok=True)
        raise

    await session.refresh(document)
    return document


async def list_document_chunks(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> list[DocumentChunk]:
    await get_document(session, document_id)
    result = await session.scalars(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index),
    )
    return list(result)


async def index_document(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> dict[str, object]:
    document = await get_document(session, document_id)
    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document must be ready before indexing.",
        )

    chunks = await list_document_chunks(session, document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chunks found for this document.",
        )

    try:
        vectors = embed_texts([chunk.content for chunk in chunks])
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            point_id = str(chunk.id)
            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "document_id": str(document.id),
                        "chunk_id": str(chunk.id),
                        "workspace_id": str(document.workspace_id),
                        "user_id": str(document.user_id),
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                    },
                },
            )
            chunk.qdrant_point_id = point_id

        upsert_chunk_vectors(points)
        await session.commit()
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except QdrantServiceError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "document_id": document.id,
        "indexed_chunks": len(chunks),
        "collection": settings.qdrant_collection,
    }


async def search_document(
    session: AsyncSession,
    document_id: uuid.UUID,
    query: str,
    limit: int = 5,
) -> list[dict[str, object]]:
    document = await get_document(session, document_id)
    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document must be ready before search.",
        )

    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    chunks = await list_document_chunks(session, document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chunks found for this document.",
        )

    try:
        query_vector = embed_text(query)
        results = search_document_chunks(
            query_vector=query_vector,
            document_id=str(document.id),
            limit=limit,
        )
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except QdrantServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return [
        {
            "chunk_id": result.payload["chunk_id"],
            "document_id": result.payload["document_id"],
            "workspace_id": result.payload["workspace_id"],
            "user_id": result.payload["user_id"],
            "chunk_index": result.payload["chunk_index"],
            "content": result.payload["content"],
            "score": result.score,
            "qdrant_point_id": str(result.id),
        }
        for result in results
        if result.payload is not None
    ]


async def list_documents(
    session: AsyncSession,
    skip: int,
    limit: int,
    workspace_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc())
    if workspace_id is not None:
        statement = statement.where(Document.workspace_id == workspace_id)
    if user_id is not None:
        statement = statement.where(Document.user_id == user_id)

    result = await session.scalars(statement.offset(skip).limit(limit))
    return list(result)


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> Document:
    document = await session.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )
    return document
