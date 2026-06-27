import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    content_type: str | None
    storage_path: str
    size_bytes: int | None
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int | None
    qdrant_point_id: str | None
    created_at: datetime
    updated_at: datetime


class DocumentIndexRead(BaseModel):
    document_id: uuid.UUID
    indexed_chunks: int
    collection: str


class DocumentSearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    chunk_index: int
    content: str
    score: float
    qdrant_point_id: str
