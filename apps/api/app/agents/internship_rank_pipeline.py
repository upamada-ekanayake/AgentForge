from app.agents.context_builder import build_context
from app.agents.match_report_generator import generate_match_report
from app.agents.retrieval_quality import build_retrieval_quality
from app.agents.retriever_agent import build_retriever_output
from app.modules.agents.schemas import (
    ContextBuilderInput,
    InternshipRankPipelineOutput,
    InternshipSummary,
    MatchReportInput,
    PlannerTaskType,
    RankedInternshipResult,
)
from app.modules.internships.models import InternshipPost


DEFAULT_RANK_QUERY = "backend internship AI internship software engineering internship"


def build_rank_search_query(base_query: str, internship_post: InternshipPost) -> str:
    return " ".join(
        part.strip()
        for part in [
            base_query,
            internship_post.title,
            internship_post.description,
            internship_post.requirements or "",
        ]
        if part and part.strip()
    )


def build_ranked_result(
    internship_post: InternshipPost,
    cv_chunks: list[dict[str, object]],
    workspace_id,
    user_id,
) -> RankedInternshipResult:
    retrieval = build_retriever_output(cv_chunks, internship_post)
    context = build_context(
        ContextBuilderInput(
            workspace_id=workspace_id,
            user_id=user_id,
            cv_chunks=retrieval.cv_chunks,
            internship_post=retrieval.internship_post,
            task_type=PlannerTaskType.COMPARE_CV_TO_INTERNSHIP,
        ),
    )
    report = generate_match_report(
        MatchReportInput(
            workspace_id=workspace_id,
            user_id=user_id,
            context_text=context.context_text,
            cv_evidence=context.cv_evidence,
            internship_summary=InternshipSummary(
                title=internship_post.title,
                company_name=internship_post.company_name,
                location=internship_post.location,
                description=internship_post.description,
                requirements=internship_post.requirements,
            ),
            source_chunk_ids=context.source_chunk_ids,
        ),
    )

    return RankedInternshipResult(
        rank=0,
        internship_post_id=internship_post.id,
        title=internship_post.title,
        company_name=internship_post.company_name,
        match_score=report.match_score,
        matched_skills=report.matched_skills,
        missing_skills=report.missing_skills,
        retrieval_quality=build_retrieval_quality(
            [chunk.score for chunk in retrieval.cv_chunks],
        ),
        recommendations=report.recommendations,
    )


def build_rank_pipeline_output(
    query: str,
    results: list[RankedInternshipResult],
) -> InternshipRankPipelineOutput:
    ranked_results = sorted(
        results,
        key=lambda result: (
            result.match_score,
            result.retrieval_quality.top_score or 0,
            result.title,
        ),
        reverse=True,
    )
    for index, result in enumerate(ranked_results, start=1):
        result.rank = index

    return InternshipRankPipelineOutput(
        query=query,
        total_ranked=len(ranked_results),
        results=ranked_results,
    )
