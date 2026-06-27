import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.agents.schemas import (
    ContextBuilderOutput,
    EvidenceAnalyzerOutput,
    LLMReasonerOutput,
    MatchReportOutput,
    OutputValidationOutput,
    PlannerOutput,
    RetrieverOutput,
)


class PipelineStageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineWarning(BaseModel):
    stage: str
    message: str
    code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PipelineError(BaseModel):
    stage: str
    message: str
    code: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InternshipPipelineState(BaseModel):
    user_query: str
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    internship_post_id: uuid.UUID
    plan: PlannerOutput | None = None
    retrieval: RetrieverOutput | None = None
    evidence: EvidenceAnalyzerOutput | None = None
    context: ContextBuilderOutput | None = None
    deterministic_report: MatchReportOutput | None = None
    llm_reasoning: LLMReasonerOutput | None = None
    validation: OutputValidationOutput | None = None
    warnings: list[PipelineWarning] = Field(default_factory=list)
    errors: list[PipelineError] = Field(default_factory=list)
    current_stage: str | None = None
    completed_stages: list[str] = Field(default_factory=list)

    def mark_stage_running(self, stage: str) -> None:
        self.current_stage = stage

    def mark_stage_completed(self, stage: str) -> None:
        self.current_stage = None
        if stage not in self.completed_stages:
            self.completed_stages.append(stage)

    def add_warning(
        self,
        stage: str,
        message: str,
        code: str | None = None,
    ) -> None:
        self.warnings.append(
            PipelineWarning(stage=stage, message=message, code=code),
        )

    def add_error(
        self,
        stage: str,
        message: str,
        code: str | None = None,
    ) -> None:
        self.errors.append(
            PipelineError(stage=stage, message=message, code=code),
        )


class InternshipMatchGraphRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    final_state: InternshipPipelineState
    completed_stages: list[str]
    warnings: list[PipelineWarning]
    errors: list[PipelineError]
    deterministic_report: MatchReportOutput | None
