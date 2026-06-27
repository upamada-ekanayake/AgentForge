import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentRunStatus


class PlannerTaskType(StrEnum):
    COMPARE_CV_TO_INTERNSHIP = "compare_cv_to_internship"
    GENERATE_COVER_LETTER = "generate_cover_letter"
    PREPARE_INTERVIEW_QUESTIONS = "prepare_interview_questions"
    UNKNOWN = "unknown"


class PlannerOutputFormat(StrEnum):
    INTERNSHIP_MATCH_REPORT = "internship_match_report"
    COVER_LETTER_DRAFT = "cover_letter_draft"
    INTERVIEW_PREP_GUIDE = "interview_prep_guide"


class RetrievalQualityLevel(StrEnum):
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"


class ValidationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AgentRegistryItem(BaseModel):
    agent_name: str
    run_type: str
    description: str
    enabled: bool


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    application_id: uuid.UUID | None
    run_type: str
    status: AgentRunStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgentRunDetail(AgentRunRead):
    input_payload: dict[str, Any] | None
    output_payload: dict[str, Any] | None


class PlannerInput(BaseModel):
    user_query: str = Field(min_length=1)
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID | None = None
    internship_post_id: uuid.UUID | None = None


class PlannerOutput(BaseModel):
    task_type: PlannerTaskType
    confidence: float = Field(ge=0, le=1)
    required_context: list[str]
    steps: list[str]
    output_format: PlannerOutputFormat | None
    needs_clarification: bool
    clarifying_question: str | None


class PlannerRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    plan: PlannerOutput


class RetrieverInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    internship_post_id: uuid.UUID
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    chunk_index: int
    content: str
    score: float
    qdrant_point_id: str


class RetrievedInternshipPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_by_id: uuid.UUID
    title: str
    company_name: str
    location: str | None
    description: str
    requirements: str | None
    source_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RetrieverOutput(BaseModel):
    cv_chunks: list[RetrievedChunk]
    internship_post: RetrievedInternshipPost


class RetrieverRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    retrieval: RetrieverOutput


class RetrievalSummary(BaseModel):
    cv_chunk_count: int
    top_score: float | None
    internship_post_id: uuid.UUID
    internship_title: str
    internship_company: str


class RetrievalQuality(BaseModel):
    top_score: float | None
    average_score: float | None
    quality_level: RetrievalQualityLevel
    warning: str | None


class ContextSummary(BaseModel):
    source_chunk_count: int
    source_chunk_ids: list[uuid.UUID]
    context_preview: str


class EvidenceSummary(BaseModel):
    kept_chunk_count: int
    discarded_chunk_count: int
    warnings: list[str]


class EvidenceAnalyzerInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    cv_chunks: list[RetrievedChunk]
    min_score: float = Field(default=0.45, ge=0, le=1)
    max_chunks: int = Field(default=3, ge=1, le=20)


class AnalyzedEvidenceChunk(RetrievedChunk):
    decision: str
    reason: str


class EvidenceAnalyzerOutput(BaseModel):
    kept_chunks: list[AnalyzedEvidenceChunk]
    discarded_chunks: list[AnalyzedEvidenceChunk]
    retrieval_quality: RetrievalQuality
    warnings: list[str]


class EvidenceAnalyzerRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    evidence: EvidenceAnalyzerOutput


class ContextBuilderInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    cv_chunks: list[RetrievedChunk]
    internship_post: RetrievedInternshipPost
    task_type: PlannerTaskType


class InternshipSummary(BaseModel):
    title: str
    company_name: str
    location: str | None
    description: str
    requirements: str | None


class ContextBuilderOutput(BaseModel):
    task_type: PlannerTaskType
    context_text: str
    cv_evidence: list[str]
    internship_summary: InternshipSummary
    source_chunk_ids: list[uuid.UUID]


class ContextBuilderRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    context: ContextBuilderOutput


class MatchReportInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    context_text: str = Field(min_length=1)
    cv_evidence: list[str]
    internship_summary: InternshipSummary
    source_chunk_ids: list[uuid.UUID]


class SkillMatch(BaseModel):
    skill: str
    evidence: str
    category: str | None = None
    match_type: str = "direct"
    confidence: float = Field(default=1.0, ge=0, le=1)


class SkillGap(BaseModel):
    skill: str
    recommendation: str
    category: str | None = None


class MatchReportOutput(BaseModel):
    match_score: float = Field(ge=0, le=100)
    summary: str
    matched_skills: list[SkillMatch]
    missing_skills: list[SkillGap]
    recommendations: list[str]
    source_chunk_ids: list[uuid.UUID]


class MatchReportRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    report: MatchReportOutput


class LLMReasonerInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    context_text: str = Field(min_length=1)
    deterministic_report: MatchReportOutput


class LLMReasonerOutput(BaseModel):
    prompt_name: str
    prompt_version: str
    reasoning_summary: str = Field(min_length=1)
    strengths: list[str]
    weaknesses: list[str]
    improvement_plan: list[str]
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[str]


class LLMReasonerRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    reasoning: LLMReasonerOutput


class OutputValidationFinding(BaseModel):
    code: str
    severity: ValidationSeverity
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class OutputValidationInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    deterministic_report: MatchReportOutput
    llm_reasoning: LLMReasonerOutput
    retrieval_quality: RetrievalQuality | None = None
    llm_match_score: float | None = Field(default=None, ge=0, le=100)


class OutputValidationOutput(BaseModel):
    is_valid: bool
    deterministic_score: float
    llm_score: float | None
    score_delta: float | None
    findings: list[OutputValidationFinding]


class OutputValidationRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    validation: OutputValidationOutput


class InternshipMatchPipelineInput(BaseModel):
    user_query: str = Field(min_length=1)
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    internship_post_id: uuid.UUID


class InternshipMatchPipelineOutput(BaseModel):
    planner_agent_run_id: uuid.UUID | None
    retriever_agent_run_id: uuid.UUID | None
    evidence_analyzer_agent_run_id: uuid.UUID | None
    context_builder_agent_run_id: uuid.UUID | None
    match_report_agent_run_id: uuid.UUID | None
    plan: PlannerOutput
    retrieval_summary: RetrievalSummary | None
    retrieval_quality: RetrievalQuality | None
    evidence_summary: EvidenceSummary | None
    context_summary: ContextSummary | None
    report: MatchReportOutput | None
    needs_clarification: bool
    clarifying_question: str | None
    stopped_reason: str | None


class InternshipMatchPipelineRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    pipeline: InternshipMatchPipelineOutput


class InternshipRankPipelineInput(BaseModel):
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    query: str | None = None


class RankedInternshipResult(BaseModel):
    rank: int
    internship_post_id: uuid.UUID
    title: str
    company_name: str
    match_score: float = Field(ge=0, le=100)
    matched_skills: list[SkillMatch]
    missing_skills: list[SkillGap]
    retrieval_quality: RetrievalQuality
    recommendations: list[str]


class InternshipRankPipelineOutput(BaseModel):
    query: str
    total_ranked: int
    results: list[RankedInternshipResult]


class InternshipRankPipelineRunResponse(BaseModel):
    agent_run_id: uuid.UUID
    ranking: InternshipRankPipelineOutput
