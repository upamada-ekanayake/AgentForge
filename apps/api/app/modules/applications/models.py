import uuid

from sqlalchemy import Enum, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ApplicationStatus, enum_values
from app.models.mixins import BaseModelMixin


class Application(BaseModelMixin, Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            "internship_post_id",
            name="uq_applications_workspace_user_post",
        ),
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
    internship_post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("internship_posts.id", ondelete="CASCADE"),
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", values_callable=enum_values),
        default=ApplicationStatus.DRAFT,
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(Float, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    workspace: Mapped["Workspace"] = relationship(back_populates="applications")
    user: Mapped["User"] = relationship(back_populates="applications")
    internship_post: Mapped["InternshipPost"] = relationship(
        back_populates="applications",
    )
    document: Mapped["Document"] = relationship()
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="application")
