import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.internships.models import InternshipPost
from app.modules.internships.schemas import InternshipPostCreate, InternshipPostUpdate
from app.modules.workspaces.service import ensure_workspace_access


async def create_internship_post(
    session: AsyncSession,
    payload: InternshipPostCreate,
) -> InternshipPost:
    await ensure_workspace_access(session, payload.workspace_id, payload.created_by_id)

    internship_post = InternshipPost(**payload.model_dump())
    session.add(internship_post)
    await session.commit()
    await session.refresh(internship_post)
    return internship_post


async def list_internship_posts(
    session: AsyncSession,
    skip: int,
    limit: int,
    workspace_id: uuid.UUID | None = None,
    is_active: bool | None = None,
) -> list[InternshipPost]:
    statement = select(InternshipPost).order_by(InternshipPost.created_at.desc())
    if workspace_id is not None:
        statement = statement.where(InternshipPost.workspace_id == workspace_id)
    if is_active is not None:
        statement = statement.where(InternshipPost.is_active == is_active)

    result = await session.scalars(statement.offset(skip).limit(limit))
    return list(result)


async def list_active_workspace_internship_posts(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[InternshipPost]:
    result = await session.scalars(
        select(InternshipPost)
        .where(InternshipPost.workspace_id == workspace_id)
        .where(InternshipPost.is_active.is_(True))
        .order_by(InternshipPost.created_at.desc()),
    )
    return list(result)


async def get_internship_post(
    session: AsyncSession,
    internship_id: uuid.UUID,
) -> InternshipPost:
    internship_post = await session.get(InternshipPost, internship_id)
    if internship_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship post not found.",
        )
    return internship_post


async def update_internship_post(
    session: AsyncSession,
    internship_id: uuid.UUID,
    payload: InternshipPostUpdate,
    request_user_id: uuid.UUID,
) -> InternshipPost:
    internship_post = await get_internship_post(session, internship_id)
    await ensure_workspace_access(
        session,
        internship_post.workspace_id,
        request_user_id,
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(internship_post, field, value)

    await session.commit()
    await session.refresh(internship_post)
    return internship_post


async def delete_internship_post(
    session: AsyncSession,
    internship_id: uuid.UUID,
    request_user_id: uuid.UUID,
) -> None:
    internship_post = await get_internship_post(session, internship_id)
    await ensure_workspace_access(
        session,
        internship_post.workspace_id,
        request_user_id,
    )

    await session.delete(internship_post)
    await session.commit()
