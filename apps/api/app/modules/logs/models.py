import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AgentLogLevel, enum_values
from app.models.mixins import BaseModelMixin


class AgentLog(BaseModelMixin, Base):
    __tablename__ = "agent_logs"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        index=True,
    )
    agent_step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_steps.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    level: Mapped[AgentLogLevel] = mapped_column(
        Enum(AgentLogLevel, name="agent_log_level", values_callable=enum_values),
        default=AgentLogLevel.INFO,
        nullable=False,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)

    agent_run: Mapped["AgentRun"] = relationship(back_populates="logs")
    agent_step: Mapped["AgentStep"] = relationship(back_populates="logs")
