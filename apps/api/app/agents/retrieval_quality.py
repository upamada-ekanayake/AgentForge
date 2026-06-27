from app.modules.agents.schemas import RetrievalQuality, RetrievalQualityLevel


WEAK_RETRIEVAL_WARNING = (
    "Retrieved CV evidence may be weak. Upload a better CV or improve the query."
)


def build_retrieval_quality(scores: list[float]) -> RetrievalQuality:
    top_score = _top_score(scores)
    average_score = _average_score(scores)

    if top_score is None:
        return RetrievalQuality(
            top_score=None,
            average_score=None,
            quality_level=RetrievalQualityLevel.WEAK,
            warning="No CV evidence was retrieved. Upload a better CV or improve the query.",
        )

    if top_score >= 0.65:
        quality_level = RetrievalQualityLevel.STRONG
    elif top_score >= 0.45:
        quality_level = RetrievalQualityLevel.MEDIUM
    else:
        quality_level = RetrievalQualityLevel.WEAK

    return RetrievalQuality(
        top_score=round(top_score, 3),
        average_score=average_score,
        quality_level=quality_level,
        warning=WEAK_RETRIEVAL_WARNING
        if quality_level == RetrievalQualityLevel.WEAK
        else None,
    )


def top_score(scores: list[float]) -> float | None:
    return _top_score(scores)


def _top_score(scores: list[float]) -> float | None:
    if not scores:
        return None
    return max(scores)


def _average_score(scores: list[float]) -> float | None:
    if not scores:
        return None
    return round(sum(scores) / len(scores), 3)
