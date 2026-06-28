import uuid
from collections.abc import Callable

import pytest

from app.modules.agents.schemas import (
    EvidenceAnalyzerInput,
    InternshipSummary,
    LLMReasonerOutput,
    MatchReportInput,
    MatchReportOutput,
    OutputValidationInput,
    PlannerInput,
    RetrievedChunk,
    RetrievalQuality,
    RetrievalQualityLevel,
    SkillGap,
)


WORKSPACE_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("10000000-0000-0000-0000-000000000002")
DOCUMENT_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
INTERNSHIP_POST_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")


@pytest.fixture
def make_planner_input() -> Callable[[str], PlannerInput]:
    def factory(query: str) -> PlannerInput:
        return PlannerInput(
            user_query=query,
            workspace_id=WORKSPACE_ID,
            user_id=USER_ID,
            document_id=DOCUMENT_ID,
            internship_post_id=INTERNSHIP_POST_ID,
        )

    return factory


@pytest.fixture
def make_retrieved_chunk() -> Callable[[int, float, str], RetrievedChunk]:
    def factory(index: int, score: float, content: str) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=uuid.UUID(f"10000000-0000-0000-0000-{index:012d}"),
            document_id=DOCUMENT_ID,
            workspace_id=WORKSPACE_ID,
            user_id=USER_ID,
            chunk_index=index,
            content=content,
            score=score,
            qdrant_point_id=f"point-{index}",
        )

    return factory


@pytest.fixture
def make_evidence_input() -> Callable[
    [list[RetrievedChunk], float, int],
    EvidenceAnalyzerInput,
]:
    def factory(
        chunks: list[RetrievedChunk],
        min_score: float = 0.45,
        max_chunks: int = 3,
    ) -> EvidenceAnalyzerInput:
        return EvidenceAnalyzerInput(
            workspace_id=WORKSPACE_ID,
            user_id=USER_ID,
            cv_chunks=chunks,
            min_score=min_score,
            max_chunks=max_chunks,
        )

    return factory


@pytest.fixture
def make_match_report_input() -> Callable[
    [list[str], str, str | None, list[uuid.UUID] | None],
    MatchReportInput,
]:
    def factory(
        cv_evidence: list[str],
        description: str,
        requirements: str | None = None,
        source_chunk_ids: list[uuid.UUID] | None = None,
    ) -> MatchReportInput:
        return MatchReportInput(
            workspace_id=WORKSPACE_ID,
            user_id=USER_ID,
            context_text="Test context",
            cv_evidence=cv_evidence,
            internship_summary=InternshipSummary(
                title="Backend Intern",
                company_name="AgentForge Labs",
                location="Remote",
                description=description,
                requirements=requirements,
            ),
            source_chunk_ids=source_chunk_ids
            or [uuid.UUID("10000000-0000-0000-0000-000000000101")],
        )

    return factory


@pytest.fixture
def make_match_report_output() -> Callable[
    [float, list[SkillGap] | None],
    MatchReportOutput,
]:
    def factory(
        match_score: float = 82.0,
        missing_skills: list[SkillGap] | None = None,
    ) -> MatchReportOutput:
        return MatchReportOutput(
            match_score=match_score,
            summary="Deterministic summary",
            matched_skills=[],
            missing_skills=missing_skills or [],
            recommendations=[],
            source_chunk_ids=[uuid.UUID("10000000-0000-0000-0000-000000000301")],
        )

    return factory


@pytest.fixture
def make_llm_reasoning() -> Callable[
    [float, list[str] | None, list[str] | None],
    LLMReasonerOutput,
]:
    def factory(
        confidence: float = 0.7,
        weaknesses: list[str] | None = None,
        risk_flags: list[str] | None = None,
    ) -> LLMReasonerOutput:
        return LLMReasonerOutput(
            prompt_name="internship_reasoning",
            prompt_version="v1",
            reasoning_summary="Reasoning summary",
            strengths=[],
            weaknesses=weaknesses or [],
            improvement_plan=[],
            confidence=confidence,
            risk_flags=risk_flags or [],
        )

    return factory


@pytest.fixture
def make_retrieval_quality() -> Callable[
    [RetrievalQualityLevel, str | None],
    RetrievalQuality,
]:
    def factory(
        quality_level: RetrievalQualityLevel = RetrievalQualityLevel.MEDIUM,
        warning: str | None = None,
    ) -> RetrievalQuality:
        return RetrievalQuality(
            top_score=0.4 if quality_level == RetrievalQualityLevel.WEAK else 0.6,
            average_score=0.4 if quality_level == RetrievalQualityLevel.WEAK else 0.6,
            quality_level=quality_level,
            warning=warning,
        )

    return factory


@pytest.fixture
def make_output_validation_input() -> Callable[
    [
        MatchReportOutput,
        LLMReasonerOutput,
        RetrievalQuality | None,
        float | None,
    ],
    OutputValidationInput,
]:
    def factory(
        deterministic_report: MatchReportOutput,
        llm_reasoning: LLMReasonerOutput,
        retrieval_quality: RetrievalQuality | None = None,
        llm_match_score: float | None = None,
    ) -> OutputValidationInput:
        return OutputValidationInput(
            workspace_id=WORKSPACE_ID,
            user_id=USER_ID,
            deterministic_report=deterministic_report,
            llm_reasoning=llm_reasoning,
            retrieval_quality=retrieval_quality,
            llm_match_score=llm_match_score,
        )

    return factory


import httpx
from app.core.database import AsyncSessionLocal, engine, get_db_session
from app.main import app

@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture
async def db_session():
    async with engine.connect() as conn:
        transaction = await conn.begin()
        async with AsyncSessionLocal(bind=conn) as session:
            yield session
            await transaction.rollback()

@pytest.fixture
async def client(db_session):
    async def override_get_db_session():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

