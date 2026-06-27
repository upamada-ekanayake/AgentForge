import uuid

from fastapi import APIRouter
from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.modules.users import service
from app.modules.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    return await service.create_user(session, payload)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> UserRead:
    return await service.get_user(session, user_id)
