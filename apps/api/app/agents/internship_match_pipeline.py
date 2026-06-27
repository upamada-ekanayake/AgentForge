from app.modules.agents.schemas import (
    ContextBuilderRunResponse,
    ContextSummary,
    EvidenceAnalyzerRunResponse,
    EvidenceSummary,
    InternshipMatchPipelineOutput,
    MatchReportRunResponse,
    PlannerRunResponse,
    RetrievalSummary,
    RetrieverRunResponse,
)
from app.agents.retrieval_quality import build_retrieval_quality, top_score


def build_clarification_pipeline_output(
    planner_response: PlannerRunResponse,
) -> InternshipMatchPipelineOutput:
    return InternshipMatchPipelineOutput(
        planner_agent_run_id=planner_response.agent_run_id,
        retriever_agent_run_id=None,
        evidence_analyzer_agent_run_id=None,
        context_builder_agent_run_id=None,
        match_report_agent_run_id=None,
        plan=planner_response.plan,
        retrieval_summary=None,
        retrieval_quality=None,
        evidence_summary=None,
        context_summary=None,
        report=None,
        needs_clarification=True,
        clarifying_question=planner_response.plan.clarifying_question,
        stopped_reason="planner_needs_clarification",
    )


def build_completed_pipeline_output(
    planner_response: PlannerRunResponse,
    retriever_response: RetrieverRunResponse,
    evidence_response: EvidenceAnalyzerRunResponse,
    context_response: ContextBuilderRunResponse,
    match_report_response: MatchReportRunResponse,
) -> InternshipMatchPipelineOutput:
    retrieval = retriever_response.retrieval
    evidence = evidence_response.evidence
    context = context_response.context
    retrieval_scores = [chunk.score for chunk in retrieval.cv_chunks]

    return InternshipMatchPipelineOutput(
        planner_agent_run_id=planner_response.agent_run_id,
        retriever_agent_run_id=retriever_response.agent_run_id,
        evidence_analyzer_agent_run_id=evidence_response.agent_run_id,
        context_builder_agent_run_id=context_response.agent_run_id,
        match_report_agent_run_id=match_report_response.agent_run_id,
        plan=planner_response.plan,
        retrieval_summary=RetrievalSummary(
            cv_chunk_count=len(retrieval.cv_chunks),
            top_score=top_score(retrieval_scores),
            internship_post_id=retrieval.internship_post.id,
            internship_title=retrieval.internship_post.title,
            internship_company=retrieval.internship_post.company_name,
        ),
        retrieval_quality=evidence.retrieval_quality,
        evidence_summary=EvidenceSummary(
            kept_chunk_count=len(evidence.kept_chunks),
            discarded_chunk_count=len(evidence.discarded_chunks),
            warnings=evidence.warnings,
        ),
        context_summary=ContextSummary(
            source_chunk_count=len(context.source_chunk_ids),
            source_chunk_ids=context.source_chunk_ids,
            context_preview=_preview(context.context_text),
        ),
        report=match_report_response.report,
        needs_clarification=False,
        clarifying_question=None,
        stopped_reason=None,
    )


def build_no_reliable_evidence_pipeline_output(
    planner_response: PlannerRunResponse,
    retriever_response: RetrieverRunResponse,
    evidence_response: EvidenceAnalyzerRunResponse,
) -> InternshipMatchPipelineOutput:
    retrieval = retriever_response.retrieval
    evidence = evidence_response.evidence
    retrieval_scores = [chunk.score for chunk in retrieval.cv_chunks]

    return InternshipMatchPipelineOutput(
        planner_agent_run_id=planner_response.agent_run_id,
        retriever_agent_run_id=retriever_response.agent_run_id,
        evidence_analyzer_agent_run_id=evidence_response.agent_run_id,
        context_builder_agent_run_id=None,
        match_report_agent_run_id=None,
        plan=planner_response.plan,
        retrieval_summary=RetrievalSummary(
            cv_chunk_count=len(retrieval.cv_chunks),
            top_score=top_score(retrieval_scores),
            internship_post_id=retrieval.internship_post.id,
            internship_title=retrieval.internship_post.title,
            internship_company=retrieval.internship_post.company_name,
        ),
        retrieval_quality=evidence.retrieval_quality,
        evidence_summary=EvidenceSummary(
            kept_chunk_count=0,
            discarded_chunk_count=len(evidence.discarded_chunks),
            warnings=evidence.warnings,
        ),
        context_summary=None,
        report=None,
        needs_clarification=False,
        clarifying_question=None,
        stopped_reason="no_reliable_evidence",
    )


def _preview(text: str, max_length: int = 500) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length].rstrip()}..."
