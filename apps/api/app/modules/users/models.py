from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class User(BaseModelMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owned_workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="user")
    internship_posts: Mapped[list["InternshipPost"]] = relationship(
        back_populates="created_by",
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="user")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="user")
