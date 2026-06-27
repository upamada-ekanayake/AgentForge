import re
from hashlib import sha256

from app.agents.retrieval_quality import build_retrieval_quality
from app.modules.agents.schemas import (
    AnalyzedEvidenceChunk,
    EvidenceAnalyzerInput,
    EvidenceAnalyzerOutput,
    RetrievedChunk,
)


DEFAULT_MIN_SCORE = 0.45
DEFAULT_MAX_CHUNKS = 3


def analyze_evidence(
    analyzer_input: EvidenceAnalyzerInput,
) -> EvidenceAnalyzerOutput:
    min_score = analyzer_input.min_score
    max_chunks = analyzer_input.max_chunks
    sorted_chunks = sorted(
        analyzer_input.cv_chunks,
        key=lambda chunk: chunk.score,
        reverse=True,
    )

    kept_chunks: list[AnalyzedEvidenceChunk] = []
    discarded_chunks: list[AnalyzedEvidenceChunk] = []
    seen_hashes: set[str] = set()

    for chunk in sorted_chunks:
        content_hash = _content_hash(chunk.content)
        if content_hash in seen_hashes:
            discarded_chunks.append(
                _to_analyzed_chunk(
                    chunk,
                    decision="discarded",
                    reason="Duplicate or near-duplicate evidence.",
                ),
            )
            continue

        seen_hashes.add(content_hash)

        if chunk.score < min_score:
            discarded_chunks.append(
                _to_analyzed_chunk(
                    chunk,
                    decision="discarded",
                    reason=f"Retrieval score is below {min_score:.2f}.",
                ),
            )
            continue

        if len(kept_chunks) >= max_chunks:
            discarded_chunks.append(
                _to_analyzed_chunk(
                    chunk,
                    decision="discarded",
                    reason=f"Lower-ranked evidence beyond top {max_chunks}.",
                ),
            )
            continue

        kept_chunks.append(
            _to_analyzed_chunk(
                chunk,
                decision="kept",
                reason="Relevant evidence retained for context building.",
            ),
        )

    warnings = _build_warnings(
        kept_chunks=kept_chunks,
        discarded_chunks=discarded_chunks,
        min_score=min_score,
    )

    return EvidenceAnalyzerOutput(
        kept_chunks=kept_chunks,
        discarded_chunks=discarded_chunks,
        retrieval_quality=build_retrieval_quality(
            [chunk.score for chunk in analyzer_input.cv_chunks],
        ),
        warnings=warnings,
    )


def _to_analyzed_chunk(
    chunk: RetrievedChunk,
    decision: str,
    reason: str,
) -> AnalyzedEvidenceChunk:
    return AnalyzedEvidenceChunk(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        workspace_id=chunk.workspace_id,
        user_id=chunk.user_id,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        score=chunk.score,
        qdrant_point_id=chunk.qdrant_point_id,
        decision=decision,
        reason=reason,
    )


def _build_warnings(
    kept_chunks: list[AnalyzedEvidenceChunk],
    discarded_chunks: list[AnalyzedEvidenceChunk],
    min_score: float,
) -> list[str]:
    warnings: list[str] = []

    if not kept_chunks:
        warnings.append(
            "No retrieved chunks passed the evidence threshold.",
        )
    elif kept_chunks[0].score < 0.65:
        warnings.append(
            "Top retained evidence is below the strong retrieval threshold.",
        )

    discarded_for_score = [
        chunk
        for chunk in discarded_chunks
        if chunk.reason == f"Retrieval score is below {min_score:.2f}."
    ]
    if discarded_for_score:
        warnings.append(
            f"Discarded {len(discarded_for_score)} chunk(s) below the score threshold.",
        )

    return warnings


def _content_hash(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content.lower()).strip()
    return sha256(normalized.encode("utf-8")).hexdigest()
