from app.agents.retrieval_quality import (
    WEAK_RETRIEVAL_WARNING,
    build_retrieval_quality,
    top_score,
)
from app.modules.agents.schemas import RetrievalQualityLevel


def test_strong_retrieval_classification() -> None:
    # Verifies scores at or above the strong threshold are classified correctly.
    quality = build_retrieval_quality([0.65, 0.52, 0.40])

    assert quality.quality_level == RetrievalQualityLevel.STRONG
    assert quality.top_score == 0.65
    assert quality.warning is None


def test_medium_retrieval_classification() -> None:
    # Verifies scores between weak and strong thresholds are medium quality.
    quality = build_retrieval_quality([0.64, 0.45, 0.30])

    assert quality.quality_level == RetrievalQualityLevel.MEDIUM
    assert quality.top_score == 0.64
    assert quality.warning is None


def test_weak_retrieval_classification() -> None:
    # Verifies low top scores are marked weak and carry a warning.
    quality = build_retrieval_quality([0.44, 0.30, 0.10])

    assert quality.quality_level == RetrievalQualityLevel.WEAK
    assert quality.top_score == 0.44
    assert quality.warning == WEAK_RETRIEVAL_WARNING


def test_average_score_calculation_is_rounded() -> None:
    # Verifies average score is rounded to three decimals for stable output.
    quality = build_retrieval_quality([0.50, 0.60, 0.70])

    assert quality.average_score == 0.6


def test_empty_retrieval_handling() -> None:
    # Verifies no retrieved scores produce a safe weak-quality result.
    quality = build_retrieval_quality([])

    assert quality.top_score is None
    assert quality.average_score is None
    assert quality.quality_level == RetrievalQualityLevel.WEAK
    assert quality.warning == "No CV evidence was retrieved. Upload a better CV or improve the query."


def test_top_score_returns_highest_score_or_none() -> None:
    # Verifies the public top_score helper handles populated and empty lists.
    assert top_score([0.20, 0.91, 0.50]) == 0.91
    assert top_score([]) is None


def test_threshold_boundary_values() -> None:
    # Verifies exact boundary values stay in the intended quality bucket.
    strong = build_retrieval_quality([0.65])
    medium = build_retrieval_quality([0.45])
    weak = build_retrieval_quality([0.449])

    assert strong.quality_level == RetrievalQualityLevel.STRONG
    assert medium.quality_level == RetrievalQualityLevel.MEDIUM
    assert weak.quality_level == RetrievalQualityLevel.WEAK
