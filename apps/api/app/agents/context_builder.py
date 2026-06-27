from app.modules.agents.schemas import (
    ContextBuilderInput,
    ContextBuilderOutput,
    InternshipSummary,
)


def build_context(context_input: ContextBuilderInput) -> ContextBuilderOutput:
    cv_evidence = [
        _format_cv_evidence(index, chunk.content, chunk.score)
        for index, chunk in enumerate(context_input.cv_chunks, start=1)
    ]
    internship_summary = InternshipSummary(
        title=context_input.internship_post.title,
        company_name=context_input.internship_post.company_name,
        location=context_input.internship_post.location,
        description=context_input.internship_post.description,
        requirements=context_input.internship_post.requirements,
    )

    context_text = "\n\n".join(
        [
            "## Candidate CV Evidence",
            "\n".join(cv_evidence) if cv_evidence else "No CV evidence retrieved.",
            "## Internship Post",
            _format_internship_summary(internship_summary),
            "## Task",
            f"Task type: {context_input.task_type.value}",
        ],
    )

    return ContextBuilderOutput(
        task_type=context_input.task_type,
        context_text=context_text,
        cv_evidence=cv_evidence,
        internship_summary=internship_summary,
        source_chunk_ids=[chunk.chunk_id for chunk in context_input.cv_chunks],
    )


def _format_cv_evidence(index: int, content: str, score: float) -> str:
    return f"- Evidence {index} (score: {score:.3f}): {content.strip()}"


def _format_internship_summary(summary: InternshipSummary) -> str:
    lines = [
        f"Title: {summary.title}",
        f"Company: {summary.company_name}",
    ]
    if summary.location:
        lines.append(f"Location: {summary.location}")
    lines.extend(
        [
            f"Description: {summary.description}",
            f"Requirements: {summary.requirements or 'Not provided'}",
        ],
    )
    return "\n".join(lines)
