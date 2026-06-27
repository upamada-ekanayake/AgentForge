import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.documents import service
from app.modules.documents.schemas import (
    DocumentChunkRead,
    DocumentIndexRead,
    DocumentRead,
    DocumentSearchResult,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: uuid.UUID = Form(...),
    user_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    return await service.upload_document(
        session=session,
        file=file,
        workspace_id=workspace_id,
        user_id=user_id,
    )


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    workspace_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentRead]:
    return await service.list_documents(
        session=session,
        skip=skip,
        limit=limit,
        workspace_id=workspace_id,
        user_id=user_id,
    )


@router.get("/{document_id}/chunks", response_model=list[DocumentChunkRead])
async def list_document_chunks(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentChunkRead]:
    return await service.list_document_chunks(session, document_id)


@router.post("/{document_id}/index", response_model=DocumentIndexRead)
async def index_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DocumentIndexRead:
    return await service.index_document(session, document_id)


@router.get("/{document_id}/search", response_model=list[DocumentSearchResult])
async def search_document(
    document_id: uuid.UUID,
    query: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
    session: AsyncSession = Depends(get_db_session),
) -> list[DocumentSearchResult]:
    return await service.search_document(session, document_id, query, limit)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DocumentRead:
    return await service.get_document(session, document_id)
