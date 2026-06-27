import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str | None = Field(default=None, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
