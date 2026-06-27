import uuid

from fastapi import APIRouter
from fastapi import Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.workspaces import service
from app.modules.workspaces.schemas import WorkspaceCreate, WorkspaceRead

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    return await service.create_workspace(session, payload)


@router.get("", response_model=list[WorkspaceRead])
async def list_workspaces(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkspaceRead]:
    return await service.list_workspaces(session, skip, limit)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> WorkspaceRead:
    return await service.get_workspace(session, workspace_id)
