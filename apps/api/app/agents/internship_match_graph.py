from collections.abc import Awaitable, Callable

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context_builder import build_context
from app.agents.evidence_analyzer import analyze_evidence
from app.agents.match_report_generator import generate_match_report
from app.agents.pipeline_state import InternshipPipelineState
from app.agents.planner_agent import plan_task
from app.agents.retriever_agent import build_retriever_output
from app.modules.agents.schemas import (
    ContextBuilderInput,
    EvidenceAnalyzerInput,
    MatchReportInput,
    PlannerInput,
    PlannerTaskType,
)
from app.modules.documents.service import search_document
from app.modules.internships.service import get_internship_post


GraphNode = Callable[[InternshipPipelineState], Awaitable[dict[str, object]]]


def build_internship_match_graph(session: AsyncSession):
    graph = StateGraph(InternshipPipelineState)
    graph.add_node("planner_node", _planner_node())
    graph.add_node("retriever_node", _retriever_node(session))
    graph.add_node("evidence_analyzer_node", _evidence_analyzer_node())
    graph.add_node("context_builder_node", _context_builder_node())
    graph.add_node("match_report_node", _match_report_node())

    graph.add_edge(START, "planner_node")
    graph.add_conditional_edges(
        "planner_node",
        _route_after_planner,
        {
            "stop": END,
            "continue": "retriever_node",
        },
    )
    graph.add_edge("retriever_node", "evidence_analyzer_node")
    graph.add_conditional_edges(
        "evidence_analyzer_node",
        _route_after_evidence,
        {
            "stop": END,
            "continue": "context_builder_node",
        },
    )
    graph.add_edge("context_builder_node", "match_report_node")
    graph.add_edge("match_report_node", END)
    return graph.compile()


async def run_internship_match_graph(
    session: AsyncSession,
    initial_state: InternshipPipelineState,
) -> InternshipPipelineState:
    graph = build_internship_match_graph(session)
    final_state = await graph.ainvoke(initial_state.model_dump())
    return InternshipPipelineState.model_validate(final_state)


def _planner_node() -> GraphNode:
    async def node(state: InternshipPipelineState) -> dict[str, object]:
        state = _coerce_state(state)
        state.mark_stage_running("planner")
        plan = plan_task(
            PlannerInput(
                user_query=state.user_query,
                workspace_id=state.workspace_id,
                user_id=state.user_id,
                document_id=state.document_id,
                internship_post_id=state.internship_post_id,
            ),
        )
        if plan.needs_clarification:
            state.add_warning(
                stage="planner",
                message=plan.clarifying_question or "Planner needs clarification.",
                code="planner_needs_clarification",
            )
        state.plan = plan
        state.mark_stage_completed("planner")
        return state.model_dump()

    return node


def _retriever_node(session: AsyncSession) -> GraphNode:
    async def node(state: InternshipPipelineState) -> dict[str, object]:
        state = _coerce_state(state)
        state.mark_stage_running("retriever")
        cv_chunks = await search_document(
            session=session,
            document_id=state.document_id,
            query=state.user_query,
            limit=5,
        )
        internship_post = await get_internship_post(
            session,
            state.internship_post_id,
        )
        state.retrieval = build_retriever_output(cv_chunks, internship_post)
        state.mark_stage_completed("retriever")
        return state.model_dump()

    return node


def _evidence_analyzer_node() -> GraphNode:
    async def node(state: InternshipPipelineState) -> dict[str, object]:
        state = _coerce_state(state)
        state.mark_stage_running("evidence_analyzer")
        if state.retrieval is None:
            state.add_error(
                stage="evidence_analyzer",
                message="Retriever output is missing.",
                code="missing_retrieval",
            )
            return state.model_dump()

        evidence = analyze_evidence(
            EvidenceAnalyzerInput(
                workspace_id=state.workspace_id,
                user_id=state.user_id,
                cv_chunks=state.retrieval.cv_chunks,
            ),
        )
        for warning in evidence.warnings:
            state.add_warning(
                stage="evidence_analyzer",
                message=warning,
                code="evidence_warning",
            )
        if not evidence.kept_chunks:
            state.add_error(
                stage="evidence_analyzer",
                message="No retrieved chunks passed the evidence threshold.",
                code="no_reliable_evidence",
            )

        state.evidence = evidence
        state.mark_stage_completed("evidence_analyzer")
        return state.model_dump()

    return node


def _context_builder_node() -> GraphNode:
    async def node(state: InternshipPipelineState) -> dict[str, object]:
        state = _coerce_state(state)
        state.mark_stage_running("context_builder")
        if state.retrieval is None or state.evidence is None or state.plan is None:
            state.add_error(
                stage="context_builder",
                message="Required graph state is missing.",
                code="missing_context_inputs",
            )
            return state.model_dump()

        state.context = build_context(
            ContextBuilderInput(
                workspace_id=state.workspace_id,
                user_id=state.user_id,
                cv_chunks=state.evidence.kept_chunks,
                internship_post=state.retrieval.internship_post,
                task_type=state.plan.task_type,
            ),
        )
        state.mark_stage_completed("context_builder")
        return state.model_dump()

    return node


def _match_report_node() -> GraphNode:
    async def node(state: InternshipPipelineState) -> dict[str, object]:
        state = _coerce_state(state)
        state.mark_stage_running("match_report_generator")
        if state.context is None:
            state.add_error(
                stage="match_report_generator",
                message="Context Builder output is missing.",
                code="missing_context",
            )
            return state.model_dump()

        state.deterministic_report = generate_match_report(
            MatchReportInput(
                workspace_id=state.workspace_id,
                user_id=state.user_id,
                context_text=state.context.context_text,
                cv_evidence=state.context.cv_evidence,
                internship_summary=state.context.internship_summary,
                source_chunk_ids=state.context.source_chunk_ids,
            ),
        )
        state.mark_stage_completed("match_report_generator")
        return state.model_dump()

    return node


def _route_after_planner(state: InternshipPipelineState) -> str:
    state = _coerce_state(state)
    if state.plan is None:
        return "stop"
    if state.plan.needs_clarification or state.plan.task_type == PlannerTaskType.UNKNOWN:
        return "stop"
    return "continue"


def _route_after_evidence(state: InternshipPipelineState) -> str:
    state = _coerce_state(state)
    if state.evidence is None:
        return "stop"
    if not state.evidence.kept_chunks:
        return "stop"
    return "continue"


def _coerce_state(state: InternshipPipelineState | dict[str, object]) -> InternshipPipelineState:
    return InternshipPipelineState.model_validate(state)
