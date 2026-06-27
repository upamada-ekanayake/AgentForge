import uuid

from fastapi import APIRouter
from fastapi import Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.applications import service
from app.modules.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ApplicationRead:
    return await service.create_application(session, payload)


@router.get("", response_model=list[ApplicationRead])
async def list_applications(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    workspace_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ApplicationRead]:
    return await service.list_applications(
        session,
        skip,
        limit,
        workspace_id,
        user_id,
    )


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ApplicationRead:
    return await service.get_application(session, application_id)


@router.patch("/{application_id}", response_model=ApplicationRead)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    request_user_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> ApplicationRead:
    return await service.update_application(
        session,
        application_id,
        payload,
        request_user_id,
    )
