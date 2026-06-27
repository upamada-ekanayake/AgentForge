import uuid

from fastapi import APIRouter
from fastapi import Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.internships import service
from app.modules.internships.schemas import (
    InternshipPostCreate,
    InternshipPostRead,
    InternshipPostUpdate,
)

router = APIRouter(prefix="/internships", tags=["internships"])


@router.post("", response_model=InternshipPostRead, status_code=status.HTTP_201_CREATED)
async def create_internship_post(
    payload: InternshipPostCreate,
    session: AsyncSession = Depends(get_db_session),
) -> InternshipPostRead:
    return await service.create_internship_post(session, payload)


@router.get("", response_model=list[InternshipPostRead])
async def list_internship_posts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    workspace_id: uuid.UUID | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[InternshipPostRead]:
    return await service.list_internship_posts(
        session,
        skip,
        limit,
        workspace_id,
        is_active,
    )


@router.get("/{internship_id}", response_model=InternshipPostRead)
async def get_internship_post(
    internship_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> InternshipPostRead:
    return await service.get_internship_post(session, internship_id)


@router.patch("/{internship_id}", response_model=InternshipPostRead)
async def update_internship_post(
    internship_id: uuid.UUID,
    payload: InternshipPostUpdate,
    request_user_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> InternshipPostRead:
    return await service.update_internship_post(
        session,
        internship_id,
        payload,
        request_user_id,
    )


@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internship_post(
    internship_id: uuid.UUID,
    request_user_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await service.delete_internship_post(session, internship_id, request_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
