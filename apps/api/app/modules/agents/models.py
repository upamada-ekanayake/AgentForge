import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AgentRunStatus, AgentStepStatus, enum_values
from app.models.mixins import BaseModelMixin


class AgentRun(BaseModelMixin, Base):
    __tablename__ = "agent_runs"

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
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    run_type: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus, name="agent_run_status", values_callable=enum_values),
        default=AgentRunStatus.PENDING,
        nullable=False,
        index=True,
    )
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workspace: Mapped["Workspace"] = relationship(back_populates="agent_runs")
    user: Mapped["User"] = relationship(back_populates="agent_runs")
    application: Mapped["Application"] = relationship(
        back_populates="agent_runs",
    )
    steps: Mapped[list["AgentStep"]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )


class AgentStep(BaseModelMixin, Base):
    __tablename__ = "agent_steps"
    __table_args__ = (
        UniqueConstraint("agent_run_id", "step_order", name="uq_agent_steps_order"),
    )

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        index=True,
    )
    step_order: Mapped[int] = mapped_column(Integer)
    agent_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[AgentStepStatus] = mapped_column(
        Enum(AgentStepStatus, name="agent_step_status", values_callable=enum_values),
        default=AgentStepStatus.PENDING,
        nullable=False,
        index=True,
    )
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    agent_run: Mapped["AgentRun"] = relationship(back_populates="steps")
    logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="agent_step",
        cascade="all, delete-orphan",
    )
