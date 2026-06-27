import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import BaseModelMixin


class InternshipPost(BaseModelMixin, Base):
    __tablename__ = "internship_posts"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), index=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workspace: Mapped["Workspace"] = relationship(back_populates="internship_posts")
    created_by: Mapped["User"] = relationship(back_populates="internship_posts")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="internship_post",
    )
