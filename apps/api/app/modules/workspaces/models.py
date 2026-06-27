import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import WorkspaceRole, enum_values
from app.models.mixins import BaseModelMixin


class Workspace(BaseModelMixin, Base):
    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    owner: Mapped["User"] = relationship(back_populates="owned_workspaces")
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="workspace")
    internship_posts: Mapped[list["InternshipPost"]] = relationship(
        back_populates="workspace",
    )
    applications: Mapped[list["Application"]] = relationship(
        back_populates="workspace",
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="workspace")


class WorkspaceMember(BaseModelMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_user"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole, name="workspace_role", values_callable=enum_values),
        default=WorkspaceRole.MEMBER,
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="workspace_memberships")
