from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.agents.pipeline_state import InternshipMatchGraphRunResponse
from app.modules.agents import service
from app.modules.agents.schemas import (
    AgentRegistryItem,
    ContextBuilderInput,
    ContextBuilderRunResponse,
    EvidenceAnalyzerInput,
    EvidenceAnalyzerRunResponse,
    InternshipMatchPipelineInput,
    InternshipMatchPipelineRunResponse,
    InternshipRankPipelineInput,
    InternshipRankPipelineRunResponse,
    LLMReasonerInput,
    LLMReasonerRunResponse,
    MatchReportInput,
    MatchReportRunResponse,
    OutputValidationInput,
    OutputValidationRunResponse,
    PlannerInput,
    PlannerRunResponse,
    RetrieverInput,
    RetrieverRunResponse,
)
from app.services.agent_registry import list_agent_configs

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/registry", response_model=list[AgentRegistryItem])
async def list_agent_registry() -> list[AgentRegistryItem]:
    return [
        AgentRegistryItem.model_validate(config.model_dump())
        for config in list_agent_configs()
    ]


@router.post(
    "/planner/plan",
    response_model=PlannerRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def plan_with_planner_agent(
    planner_input: PlannerInput,
    session: AsyncSession = Depends(get_db_session),
) -> PlannerRunResponse:
    return await service.run_planner(session, planner_input)


@router.post(
    "/retriever/retrieve",
    response_model=RetrieverRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def retrieve_with_retriever_agent(
    retriever_input: RetrieverInput,
    session: AsyncSession = Depends(get_db_session),
) -> RetrieverRunResponse:
    return await service.run_retriever(session, retriever_input)


@router.post(
    "/context-builder/build",
    response_model=ContextBuilderRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def build_context_with_context_builder(
    context_input: ContextBuilderInput,
    session: AsyncSession = Depends(get_db_session),
) -> ContextBuilderRunResponse:
    return await service.run_context_builder(session, context_input)


@router.post(
    "/evidence-analyzer/analyze",
    response_model=EvidenceAnalyzerRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_with_evidence_analyzer(
    analyzer_input: EvidenceAnalyzerInput,
    session: AsyncSession = Depends(get_db_session),
) -> EvidenceAnalyzerRunResponse:
    return await service.run_evidence_analyzer(session, analyzer_input)


@router.post(
    "/match-report/generate",
    response_model=MatchReportRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_match_report(
    report_input: MatchReportInput,
    session: AsyncSession = Depends(get_db_session),
) -> MatchReportRunResponse:
    return await service.run_match_report_generator(session, report_input)


@router.post(
    "/llm-reasoner/reason",
    response_model=LLMReasonerRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def reason_with_llm_reasoner(
    reasoner_input: LLMReasonerInput,
    session: AsyncSession = Depends(get_db_session),
) -> LLMReasonerRunResponse:
    return await service.run_llm_reasoner(session, reasoner_input)


@router.post(
    "/output-validator/validate",
    response_model=OutputValidationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def validate_with_output_validator(
    validation_input: OutputValidationInput,
    session: AsyncSession = Depends(get_db_session),
) -> OutputValidationRunResponse:
    return await service.run_output_validator(session, validation_input)


@router.post(
    "/internship-match/run",
    response_model=InternshipMatchPipelineRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_internship_match_pipeline(
    pipeline_input: InternshipMatchPipelineInput,
    session: AsyncSession = Depends(get_db_session),
) -> InternshipMatchPipelineRunResponse:
    return await service.run_internship_match_pipeline(session, pipeline_input)


@router.post(
    "/internship-match-graph/run",
    response_model=InternshipMatchGraphRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_internship_match_graph_pipeline(
    pipeline_input: InternshipMatchPipelineInput,
    session: AsyncSession = Depends(get_db_session),
) -> InternshipMatchGraphRunResponse:
    return await service.run_internship_match_graph_pipeline(session, pipeline_input)


@router.post(
    "/internship-rank/run",
    response_model=InternshipRankPipelineRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_internship_rank_pipeline(
    pipeline_input: InternshipRankPipelineInput,
    session: AsyncSession = Depends(get_db_session),
) -> InternshipRankPipelineRunResponse:
    return await service.run_internship_rank_pipeline(session, pipeline_input)
