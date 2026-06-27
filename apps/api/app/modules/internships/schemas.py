import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InternshipPostCreate(BaseModel):
    workspace_id: uuid.UUID
    created_by_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    company_name: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    description: str = Field(min_length=1)
    requirements: str | None = None
    source_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class InternshipPostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    requirements: str | None = None
    source_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class InternshipPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_by_id: uuid.UUID
    title: str
    company_name: str
    location: str | None
    description: str
    requirements: str | None
    source_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
