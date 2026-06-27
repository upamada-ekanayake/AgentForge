import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApplicationStatus


class ApplicationCreate(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    internship_post_id: uuid.UUID
    document_id: uuid.UUID | None = None
    status: ApplicationStatus = ApplicationStatus.DRAFT
    match_score: float | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    document_id: uuid.UUID | None = None
    match_score: float | None = None
    notes: str | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    internship_post_id: uuid.UUID
    document_id: uuid.UUID | None
    status: ApplicationStatus
    match_score: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
