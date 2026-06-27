from collections.abc import Callable

from app.agents.evidence_analyzer import analyze_evidence
from app.modules.agents.schemas import EvidenceAnalyzerInput, RetrievedChunk


def test_keeps_highest_scoring_chunks_up_to_max_chunks(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies top-k evidence is retained after sorting by retrieval score.
    chunks = [
        make_retrieved_chunk(1, 0.51, "SQL project evidence."),
        make_retrieved_chunk(2, 0.91, "FastAPI project evidence."),
        make_retrieved_chunk(3, 0.73, "Docker project evidence."),
        make_retrieved_chunk(4, 0.68, "Git workflow evidence."),
    ]

    result = analyze_evidence(make_evidence_input(chunks, max_chunks=2))

    assert [chunk.score for chunk in result.kept_chunks] == [0.91, 0.73]
    assert [chunk.decision for chunk in result.kept_chunks] == ["kept", "kept"]
    assert len(result.discarded_chunks) == 2
    assert result.discarded_chunks[0].reason == "Lower-ranked evidence beyond top 2."


def test_discards_chunks_below_threshold(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies low-score chunks are not allowed into context building.
    chunks = [
        make_retrieved_chunk(1, 0.72, "Strong FastAPI evidence."),
        make_retrieved_chunk(2, 0.44, "Weak unrelated evidence."),
    ]

    result = analyze_evidence(make_evidence_input(chunks, min_score=0.45))

    assert [chunk.chunk_index for chunk in result.kept_chunks] == [1]
    assert [chunk.chunk_index for chunk in result.discarded_chunks] == [2]
    assert result.discarded_chunks[0].reason == "Retrieval score is below 0.45."


def test_removes_duplicate_chunks(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies duplicate content is discarded even when both scores pass.
    chunks = [
        make_retrieved_chunk(1, 0.86, "Built FastAPI APIs with PostgreSQL."),
        make_retrieved_chunk(2, 0.79, "  built fastapi APIs with   postgresql.  "),
        make_retrieved_chunk(3, 0.65, "Documented API workflows clearly."),
    ]

    result = analyze_evidence(make_evidence_input(chunks))

    assert [chunk.chunk_index for chunk in result.kept_chunks] == [1, 3]
    assert [chunk.chunk_index for chunk in result.discarded_chunks] == [2]
    assert result.discarded_chunks[0].reason == "Duplicate or near-duplicate evidence."


def test_returns_warnings_when_chunks_are_discarded_for_score(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies the analyzer explains score-based discards to callers.
    chunks = [
        make_retrieved_chunk(1, 0.62, "Medium confidence API evidence."),
        make_retrieved_chunk(2, 0.20, "Low confidence evidence."),
        make_retrieved_chunk(3, 0.10, "Very low confidence evidence."),
    ]

    result = analyze_evidence(make_evidence_input(chunks, min_score=0.45))

    assert "Top retained evidence is below the strong retrieval threshold." in result.warnings
    assert "Discarded 2 chunk(s) below the score threshold." in result.warnings


def test_returns_zero_kept_chunks_when_no_evidence_passes_threshold(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies weak retrieval produces a safe zero-evidence result.
    chunks = [
        make_retrieved_chunk(1, 0.30, "Weak evidence one."),
        make_retrieved_chunk(2, 0.25, "Weak evidence two."),
    ]

    result = analyze_evidence(make_evidence_input(chunks, min_score=0.45))

    assert result.kept_chunks == []
    assert len(result.discarded_chunks) == 2
    assert "No retrieved chunks passed the evidence threshold." in result.warnings
    assert result.retrieval_quality.quality_level == "weak"
    assert result.retrieval_quality.warning is not None


def test_preserves_kept_order_by_descending_score(
    make_retrieved_chunk: Callable[[int, float, str], RetrievedChunk],
    make_evidence_input: Callable[[list[RetrievedChunk], float, int], EvidenceAnalyzerInput],
) -> None:
    # Verifies context builder receives retained evidence in relevance order.
    chunks = [
        make_retrieved_chunk(1, 0.46, "Lowest retained evidence."),
        make_retrieved_chunk(2, 0.88, "Highest retained evidence."),
        make_retrieved_chunk(3, 0.67, "Middle retained evidence."),
    ]

    result = analyze_evidence(make_evidence_input(chunks))

    assert [chunk.chunk_index for chunk in result.kept_chunks] == [2, 3, 1]
    assert [chunk.score for chunk in result.kept_chunks] == [0.88, 0.67, 0.46]
