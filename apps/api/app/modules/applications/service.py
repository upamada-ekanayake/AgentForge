import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.applications.models import Application
from app.modules.applications.schemas import ApplicationCreate, ApplicationUpdate
from app.modules.documents.models import Document
from app.modules.internships.models import InternshipPost
from app.modules.users.models import User
from app.modules.workspaces.service import ensure_workspace_access


async def create_application(
    session: AsyncSession,
    payload: ApplicationCreate,
) -> Application:
    await ensure_workspace_access(session, payload.workspace_id, payload.user_id)

    user = await session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    internship_post = await session.get(InternshipPost, payload.internship_post_id)
    if internship_post is None or internship_post.workspace_id != payload.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship post not found in this workspace.",
        )

    if payload.document_id is not None:
        document = await session.get(Document, payload.document_id)
        if document is None or document.workspace_id != payload.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this workspace.",
            )

    existing_application = await session.scalar(
        select(Application).where(
            Application.workspace_id == payload.workspace_id,
            Application.user_id == payload.user_id,
            Application.internship_post_id == payload.internship_post_id,
        ),
    )
    if existing_application is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists for this internship.",
        )

    application = Application(**payload.model_dump())
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def list_applications(
    session: AsyncSession,
    skip: int,
    limit: int,
    workspace_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> list[Application]:
    statement = select(Application).order_by(Application.created_at.desc())
    if workspace_id is not None:
        statement = statement.where(Application.workspace_id == workspace_id)
    if user_id is not None:
        statement = statement.where(Application.user_id == user_id)

    result = await session.scalars(statement.offset(skip).limit(limit))
    return list(result)


async def get_application(
    session: AsyncSession,
    application_id: uuid.UUID,
) -> Application:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    return application


async def update_application(
    session: AsyncSession,
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    request_user_id: uuid.UUID,
) -> Application:
    application = await get_application(session, application_id)
    await ensure_workspace_access(
        session,
        application.workspace_id,
        request_user_id,
    )

    if payload.document_id is not None:
        document = await session.get(Document, payload.document_id)
        if document is None or document.workspace_id != application.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this workspace.",
            )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(application, field, value)

    await session.commit()
    await session.refresh(application)
    return application
