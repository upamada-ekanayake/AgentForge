import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WorkspaceRole
from app.modules.users.models import User
from app.modules.workspaces.models import Workspace, WorkspaceMember
from app.modules.workspaces.schemas import WorkspaceCreate


async def ensure_workspace_access(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Workspace:
    workspace = await get_workspace(session, workspace_id)
    if workspace.owner_id == user_id:
        return workspace

    membership = await session.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        ),
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this workspace.",
        )

    return workspace


async def create_workspace(
    session: AsyncSession,
    payload: WorkspaceCreate,
) -> Workspace:
    owner = await session.get(User, payload.owner_id)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace owner not found.",
        )

    workspace = Workspace(name=payload.name, owner_id=payload.owner_id)
    session.add(workspace)
    await session.flush()

    session.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=payload.owner_id,
            role=WorkspaceRole.OWNER,
        ),
    )
    await session.commit()
    await session.refresh(workspace)
    return workspace


async def list_workspaces(
    session: AsyncSession,
    skip: int,
    limit: int,
) -> list[Workspace]:
    result = await session.scalars(
        select(Workspace).order_by(Workspace.created_at.desc()).offset(skip).limit(limit),
    )
    return list(result)


async def get_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )
    return workspace
