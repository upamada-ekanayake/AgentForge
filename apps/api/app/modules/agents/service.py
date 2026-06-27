import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.context_builder import build_context
from app.agents.evidence_analyzer import analyze_evidence
from app.agents.internship_match_pipeline import (
    build_clarification_pipeline_output,
    build_completed_pipeline_output,
    build_no_reliable_evidence_pipeline_output,
)
from app.agents.internship_match_graph import run_internship_match_graph
from app.agents.internship_rank_pipeline import (
    DEFAULT_RANK_QUERY,
    build_rank_pipeline_output,
    build_rank_search_query,
    build_ranked_result,
)
from app.agents.llm_reasoner import (
    LLMProviderError,
    LLMReasonerValidationError,
    run_llm_reasoning,
)
from app.agents.match_report_generator import generate_match_report
from app.agents.output_validator import validate_reasoner_output
from app.agents.pipeline_state import (
    InternshipMatchGraphRunResponse,
    InternshipPipelineState,
)
from app.agents.planner_agent import plan_task
from app.agents.retriever_agent import build_retriever_output
from app.models.enums import AgentRunStatus
from app.modules.agents.models import AgentRun
from app.modules.agents.schemas import (
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
from app.modules.documents.service import get_document, search_document
from app.modules.internships.service import (
    get_internship_post,
    list_active_workspace_internship_posts,
)
from app.modules.users.models import User
from app.modules.workspaces.service import ensure_workspace_access


async def list_agent_runs(
    session: AsyncSession,
    skip: int,
    limit: int,
    workspace_id: uuid.UUID | None = None,
    run_type: str | None = None,
) -> list[AgentRun]:
    statement = select(AgentRun).order_by(AgentRun.created_at.desc())
    if workspace_id is not None:
        statement = statement.where(AgentRun.workspace_id == workspace_id)
    if run_type is not None:
        statement = statement.where(AgentRun.run_type == run_type)

    result = await session.scalars(statement.offset(skip).limit(limit))
    return list(result)


async def get_agent_run(session: AsyncSession, run_id: uuid.UUID) -> AgentRun:
    agent_run = await session.get(AgentRun, run_id)
    if agent_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found.",
        )
    return agent_run


async def run_planner(
    session: AsyncSession,
    planner_input: PlannerInput,
) -> PlannerRunResponse:
    await _validate_planner_scope(session, planner_input)

    agent_run = AgentRun(
        workspace_id=planner_input.workspace_id,
        user_id=planner_input.user_id,
        run_type="planner",
        status=AgentRunStatus.RUNNING,
        input_payload=planner_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        plan = plan_task(planner_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = plan.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return PlannerRunResponse(agent_run_id=agent_run.id, plan=plan)
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_retriever(
    session: AsyncSession,
    retriever_input: RetrieverInput,
) -> RetrieverRunResponse:
    await _validate_retriever_scope(session, retriever_input)

    agent_run = AgentRun(
        workspace_id=retriever_input.workspace_id,
        user_id=retriever_input.user_id,
        run_type="retriever",
        status=AgentRunStatus.RUNNING,
        input_payload=retriever_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        cv_chunks = await search_document(
            session=session,
            document_id=retriever_input.document_id,
            query=retriever_input.query,
            limit=retriever_input.limit,
        )
        internship_post = await get_internship_post(
            session,
            retriever_input.internship_post_id,
        )
        retrieval = build_retriever_output(cv_chunks, internship_post)

        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = retrieval.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return RetrieverRunResponse(agent_run_id=agent_run.id, retrieval=retrieval)
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_context_builder(
    session: AsyncSession,
    context_input: ContextBuilderInput,
) -> ContextBuilderRunResponse:
    await _validate_context_builder_scope(session, context_input)

    agent_run = AgentRun(
        workspace_id=context_input.workspace_id,
        user_id=context_input.user_id,
        run_type="context_builder",
        status=AgentRunStatus.RUNNING,
        input_payload=context_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        context = build_context(context_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = context.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return ContextBuilderRunResponse(agent_run_id=agent_run.id, context=context)
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_evidence_analyzer(
    session: AsyncSession,
    analyzer_input: EvidenceAnalyzerInput,
) -> EvidenceAnalyzerRunResponse:
    await _validate_evidence_analyzer_scope(session, analyzer_input)

    agent_run = AgentRun(
        workspace_id=analyzer_input.workspace_id,
        user_id=analyzer_input.user_id,
        run_type="evidence_analyzer",
        status=AgentRunStatus.RUNNING,
        input_payload=analyzer_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        evidence = analyze_evidence(analyzer_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = evidence.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return EvidenceAnalyzerRunResponse(
            agent_run_id=agent_run.id,
            evidence=evidence,
        )
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_match_report_generator(
    session: AsyncSession,
    report_input: MatchReportInput,
) -> MatchReportRunResponse:
    await _validate_match_report_scope(session, report_input)

    agent_run = AgentRun(
        workspace_id=report_input.workspace_id,
        user_id=report_input.user_id,
        run_type="match_report_generator",
        status=AgentRunStatus.RUNNING,
        input_payload=report_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        report = generate_match_report(report_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = report.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return MatchReportRunResponse(agent_run_id=agent_run.id, report=report)
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_llm_reasoner(
    session: AsyncSession,
    reasoner_input: LLMReasonerInput,
) -> LLMReasonerRunResponse:
    await _validate_llm_reasoner_scope(session, reasoner_input)

    agent_run = AgentRun(
        workspace_id=reasoner_input.workspace_id,
        user_id=reasoner_input.user_id,
        run_type="llm_reasoner",
        status=AgentRunStatus.RUNNING,
        input_payload=reasoner_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        reasoning = await run_llm_reasoning(reasoner_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = reasoning.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return LLMReasonerRunResponse(
            agent_run_id=agent_run.id,
            reasoning=reasoning,
        )
    except LLMProviderError as exc:
        await _mark_agent_run_failed(session, agent_run, str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMReasonerValidationError as exc:
        await _mark_agent_run_failed(session, agent_run, str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        await _mark_agent_run_failed(session, agent_run, str(exc))
        raise


async def run_output_validator(
    session: AsyncSession,
    validation_input: OutputValidationInput,
) -> OutputValidationRunResponse:
    await _validate_output_validator_scope(session, validation_input)

    agent_run = AgentRun(
        workspace_id=validation_input.workspace_id,
        user_id=validation_input.user_id,
        run_type="output_validator",
        status=AgentRunStatus.RUNNING,
        input_payload=validation_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(agent_run)
    await session.flush()

    try:
        validation = validate_reasoner_output(validation_input)
        agent_run.status = AgentRunStatus.SUCCEEDED
        agent_run.output_payload = validation.model_dump(mode="json")
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(agent_run)
        return OutputValidationRunResponse(
            agent_run_id=agent_run.id,
            validation=validation,
        )
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.output_payload = {"error": str(exc)}
        agent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_internship_match_pipeline(
    session: AsyncSession,
    pipeline_input: InternshipMatchPipelineInput,
) -> InternshipMatchPipelineRunResponse:
    parent_run = AgentRun(
        workspace_id=pipeline_input.workspace_id,
        user_id=pipeline_input.user_id,
        run_type="internship_match_pipeline",
        status=AgentRunStatus.RUNNING,
        input_payload=pipeline_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(parent_run)
    await session.commit()
    await session.refresh(parent_run)

    try:
        planner_response = await run_planner(
            session,
            PlannerInput(
                user_query=pipeline_input.user_query,
                workspace_id=pipeline_input.workspace_id,
                user_id=pipeline_input.user_id,
                document_id=pipeline_input.document_id,
                internship_post_id=pipeline_input.internship_post_id,
            ),
        )

        if (
            planner_response.plan.needs_clarification
            or planner_response.plan.task_type == "unknown"
        ):
            pipeline_output = build_clarification_pipeline_output(planner_response)
            parent_run.status = AgentRunStatus.SUCCEEDED
            parent_run.output_payload = pipeline_output.model_dump(mode="json")
            parent_run.completed_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(parent_run)
            return InternshipMatchPipelineRunResponse(
                agent_run_id=parent_run.id,
                pipeline=pipeline_output,
            )

        retriever_response = await run_retriever(
            session,
            RetrieverInput(
                workspace_id=pipeline_input.workspace_id,
                user_id=pipeline_input.user_id,
                document_id=pipeline_input.document_id,
                internship_post_id=pipeline_input.internship_post_id,
                query=pipeline_input.user_query,
            ),
        )
        evidence_response = await run_evidence_analyzer(
            session,
            EvidenceAnalyzerInput(
                workspace_id=pipeline_input.workspace_id,
                user_id=pipeline_input.user_id,
                cv_chunks=retriever_response.retrieval.cv_chunks,
            ),
        )

        if not evidence_response.evidence.kept_chunks:
            pipeline_output = build_no_reliable_evidence_pipeline_output(
                planner_response=planner_response,
                retriever_response=retriever_response,
                evidence_response=evidence_response,
            )
            parent_run.status = AgentRunStatus.SUCCEEDED
            parent_run.output_payload = pipeline_output.model_dump(mode="json")
            parent_run.completed_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(parent_run)
            return InternshipMatchPipelineRunResponse(
                agent_run_id=parent_run.id,
                pipeline=pipeline_output,
            )

        context_response = await run_context_builder(
            session,
            ContextBuilderInput(
                workspace_id=pipeline_input.workspace_id,
                user_id=pipeline_input.user_id,
                cv_chunks=evidence_response.evidence.kept_chunks,
                internship_post=retriever_response.retrieval.internship_post,
                task_type=planner_response.plan.task_type,
            ),
        )
        match_report_response = await run_match_report_generator(
            session,
            MatchReportInput(
                workspace_id=pipeline_input.workspace_id,
                user_id=pipeline_input.user_id,
                context_text=context_response.context.context_text,
                cv_evidence=context_response.context.cv_evidence,
                internship_summary=context_response.context.internship_summary,
                source_chunk_ids=context_response.context.source_chunk_ids,
            ),
        )

        pipeline_output = build_completed_pipeline_output(
            planner_response=planner_response,
            retriever_response=retriever_response,
            evidence_response=evidence_response,
            context_response=context_response,
            match_report_response=match_report_response,
        )
        parent_run.status = AgentRunStatus.SUCCEEDED
        parent_run.output_payload = pipeline_output.model_dump(mode="json")
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(parent_run)
        return InternshipMatchPipelineRunResponse(
            agent_run_id=parent_run.id,
            pipeline=pipeline_output,
        )
    except Exception as exc:
        parent_run.status = AgentRunStatus.FAILED
        parent_run.output_payload = {"error": str(exc)}
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_internship_match_graph_pipeline(
    session: AsyncSession,
    pipeline_input: InternshipMatchPipelineInput,
) -> InternshipMatchGraphRunResponse:
    await _validate_graph_pipeline_scope(session, pipeline_input)

    parent_run = AgentRun(
        workspace_id=pipeline_input.workspace_id,
        user_id=pipeline_input.user_id,
        run_type="internship_match_graph_pipeline",
        status=AgentRunStatus.RUNNING,
        input_payload=pipeline_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(parent_run)
    await session.commit()
    await session.refresh(parent_run)

    try:
        initial_state = InternshipPipelineState(
            user_query=pipeline_input.user_query,
            workspace_id=pipeline_input.workspace_id,
            user_id=pipeline_input.user_id,
            document_id=pipeline_input.document_id,
            internship_post_id=pipeline_input.internship_post_id,
        )
        final_state = await run_internship_match_graph(session, initial_state)
        parent_run.status = AgentRunStatus.SUCCEEDED
        parent_run.output_payload = final_state.model_dump(mode="json")
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(parent_run)
        return InternshipMatchGraphRunResponse(
            agent_run_id=parent_run.id,
            final_state=final_state,
            completed_stages=final_state.completed_stages,
            warnings=final_state.warnings,
            errors=final_state.errors,
            deterministic_report=final_state.deterministic_report,
        )
    except Exception as exc:
        parent_run.status = AgentRunStatus.FAILED
        parent_run.output_payload = {"error": str(exc)}
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def run_internship_rank_pipeline(
    session: AsyncSession,
    pipeline_input: InternshipRankPipelineInput,
) -> InternshipRankPipelineRunResponse:
    await _validate_rank_pipeline_scope(session, pipeline_input)

    parent_run = AgentRun(
        workspace_id=pipeline_input.workspace_id,
        user_id=pipeline_input.user_id,
        run_type="internship_rank_pipeline",
        status=AgentRunStatus.RUNNING,
        input_payload=pipeline_input.model_dump(mode="json"),
        output_payload=None,
        started_at=datetime.now(UTC),
    )
    session.add(parent_run)
    await session.commit()
    await session.refresh(parent_run)

    try:
        query = (pipeline_input.query or DEFAULT_RANK_QUERY).strip()
        if not query:
            query = DEFAULT_RANK_QUERY

        internship_posts = await list_active_workspace_internship_posts(
            session,
            pipeline_input.workspace_id,
        )
        results = []

        for internship_post in internship_posts:
            cv_chunks = await search_document(
                session=session,
                document_id=pipeline_input.document_id,
                query=build_rank_search_query(query, internship_post),
                limit=5,
            )
            results.append(
                build_ranked_result(
                    internship_post=internship_post,
                    cv_chunks=cv_chunks,
                    workspace_id=pipeline_input.workspace_id,
                    user_id=pipeline_input.user_id,
                ),
            )

        ranking = build_rank_pipeline_output(query=query, results=results)
        parent_run.status = AgentRunStatus.SUCCEEDED
        parent_run.output_payload = ranking.model_dump(mode="json")
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(parent_run)
        return InternshipRankPipelineRunResponse(
            agent_run_id=parent_run.id,
            ranking=ranking,
        )
    except Exception as exc:
        parent_run.status = AgentRunStatus.FAILED
        parent_run.output_payload = {"error": str(exc)}
        parent_run.completed_at = datetime.now(UTC)
        await session.commit()
        raise


async def _validate_planner_scope(
    session: AsyncSession,
    planner_input: PlannerInput,
) -> None:
    user = await session.get(User, planner_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planner user not found.",
        )

    await ensure_workspace_access(
        session,
        planner_input.workspace_id,
        planner_input.user_id,
    )


async def _validate_retriever_scope(
    session: AsyncSession,
    retriever_input: RetrieverInput,
) -> None:
    user = await session.get(User, retriever_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Retriever user not found.",
        )

    await ensure_workspace_access(
        session,
        retriever_input.workspace_id,
        retriever_input.user_id,
    )

    document = await get_document(session, retriever_input.document_id)
    if document.workspace_id != retriever_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document does not belong to this workspace.",
        )

    internship_post = await get_internship_post(
        session,
        retriever_input.internship_post_id,
    )
    if internship_post.workspace_id != retriever_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internship post does not belong to this workspace.",
        )


async def _validate_context_builder_scope(
    session: AsyncSession,
    context_input: ContextBuilderInput,
) -> None:
    user = await session.get(User, context_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context builder user not found.",
        )

    await ensure_workspace_access(
        session,
        context_input.workspace_id,
        context_input.user_id,
    )

    if context_input.internship_post.workspace_id != context_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internship post does not belong to this workspace.",
        )

    for chunk in context_input.cv_chunks:
        if chunk.workspace_id != context_input.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A CV chunk does not belong to this workspace.",
            )
        if chunk.user_id != context_input.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A CV chunk does not belong to this user.",
            )


async def _validate_evidence_analyzer_scope(
    session: AsyncSession,
    analyzer_input: EvidenceAnalyzerInput,
) -> None:
    user = await session.get(User, analyzer_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence analyzer user not found.",
        )

    await ensure_workspace_access(
        session,
        analyzer_input.workspace_id,
        analyzer_input.user_id,
    )

    for chunk in analyzer_input.cv_chunks:
        if chunk.workspace_id != analyzer_input.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A CV chunk does not belong to this workspace.",
            )
        if chunk.user_id != analyzer_input.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A CV chunk does not belong to this user.",
            )


async def _validate_match_report_scope(
    session: AsyncSession,
    report_input: MatchReportInput,
) -> None:
    user = await session.get(User, report_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match report user not found.",
        )

    await ensure_workspace_access(
        session,
        report_input.workspace_id,
        report_input.user_id,
    )


async def _validate_llm_reasoner_scope(
    session: AsyncSession,
    reasoner_input: LLMReasonerInput,
) -> None:
    user = await session.get(User, reasoner_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM reasoner user not found.",
        )

    await ensure_workspace_access(
        session,
        reasoner_input.workspace_id,
        reasoner_input.user_id,
    )


async def _validate_output_validator_scope(
    session: AsyncSession,
    validation_input: OutputValidationInput,
) -> None:
    user = await session.get(User, validation_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output validator user not found.",
        )

    await ensure_workspace_access(
        session,
        validation_input.workspace_id,
        validation_input.user_id,
    )


async def _validate_rank_pipeline_scope(
    session: AsyncSession,
    pipeline_input: InternshipRankPipelineInput,
) -> None:
    user = await session.get(User, pipeline_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ranking user not found.",
        )

    await ensure_workspace_access(
        session,
        pipeline_input.workspace_id,
        pipeline_input.user_id,
    )

    document = await get_document(session, pipeline_input.document_id)
    if document.workspace_id != pipeline_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document does not belong to this workspace.",
        )
    if document.user_id != pipeline_input.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document does not belong to this user.",
        )


async def _validate_graph_pipeline_scope(
    session: AsyncSession,
    pipeline_input: InternshipMatchPipelineInput,
) -> None:
    user = await session.get(User, pipeline_input.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph pipeline user not found.",
        )

    await ensure_workspace_access(
        session,
        pipeline_input.workspace_id,
        pipeline_input.user_id,
    )

    document = await get_document(session, pipeline_input.document_id)
    if document.workspace_id != pipeline_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document does not belong to this workspace.",
        )
    if document.user_id != pipeline_input.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document does not belong to this user.",
        )

    internship_post = await get_internship_post(
        session,
        pipeline_input.internship_post_id,
    )
    if internship_post.workspace_id != pipeline_input.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internship post does not belong to this workspace.",
        )


async def _mark_agent_run_failed(
    session: AsyncSession,
    agent_run: AgentRun,
    error_message: str,
) -> None:
    agent_run.status = AgentRunStatus.FAILED
    agent_run.output_payload = {"error": error_message}
    agent_run.completed_at = datetime.now(UTC)
    await session.commit()
