from app.agents.skill_graph import (
    align_skills,
    calculate_weighted_score,
    detect_skills,
    find_skill_evidence,
)


def test_detects_direct_skills() -> None:
    # Verifies canonical skill names are detected directly from text.
    detected = detect_skills("Python FastAPI PostgreSQL Git documentation")

    assert "python" in detected
    assert "fastapi" in detected
    assert "postgresql" in detected
    assert "git" in detected
    assert detected["fastapi"].matched_terms == ("fastapi", "fastapi")


def test_detects_skill_aliases() -> None:
    # Verifies aliases map to the controlled skill graph names.
    detected = detect_skills(
        "Built REST services with Postgres and clear documentation.",
    )

    assert "api" in detected
    assert "postgresql" in detected
    assert "writing" in detected
    assert "rest services" in detected["api"].matched_terms
    assert "postgres" in detected["postgresql"].matched_terms
    assert "documentation" in detected["writing"].matched_terms


def test_aligns_related_skills_when_direct_skill_is_absent() -> None:
    # Verifies related CV evidence can satisfy required skills with lower confidence.
    required = detect_skills("FastAPI and PostgreSQL required.")
    cv = detect_skills("Built REST services with SQL.")

    matched, missing = align_skills(required, cv)

    assert missing == []
    assert [(match.required_skill, match.cv_skill) for match in matched] == [
        ("fastapi", "api"),
        ("postgresql", "sql"),
    ]
    assert all(match.match_type == "related" for match in matched)


def test_confidence_values_distinguish_direct_and_related_matches() -> None:
    # Verifies direct matches stay at full confidence while related matches do not.
    direct_required = detect_skills("FastAPI required.")
    direct_cv = detect_skills("FastAPI production API experience.")
    related_required = detect_skills("FastAPI required.")
    related_cv = detect_skills("REST services and API development.")

    direct_matches, _ = align_skills(direct_required, direct_cv)
    related_matches, _ = align_skills(related_required, related_cv)

    assert direct_matches[0].match_type == "direct"
    assert direct_matches[0].confidence == 1.0
    assert related_matches[0].match_type == "related"
    assert related_matches[0].confidence == 0.9
    assert related_matches[0].confidence < direct_matches[0].confidence


def test_calculates_weighted_score_with_related_confidence() -> None:
    # Verifies scoring uses required skill weights multiplied by confidence.
    required = detect_skills("FastAPI and PostgreSQL required.")
    cv = detect_skills("Built REST services with SQL.")
    matched, _ = align_skills(required, cv)

    score = calculate_weighted_score(required, matched)

    assert score == 87.68


def test_reports_missing_skills_when_no_direct_or_related_match_exists() -> None:
    # Verifies unmatched required skills remain visible as gaps.
    required = detect_skills("FastAPI Docker Qdrant required.")
    cv = detect_skills("Python and SQL experience.")

    matched, missing = align_skills(required, cv)

    assert [(match.required_skill, match.match_type) for match in matched] == [
        ("fastapi", "related"),
    ]
    assert [skill.name for skill in missing] == ["docker", "qdrant"]


def test_unrelated_text_does_not_create_false_positives() -> None:
    # Verifies ordinary unrelated text does not accidentally match skill aliases.
    detected = detect_skills("I enjoy painting landscapes and cooking dinner.")

    assert detected == {}


def test_finds_skill_evidence_with_related_fallback() -> None:
    # Verifies evidence lookup can explain related alignments using CV skill text.
    evidence = [
        "Built REST services and API endpoints for internal tools.",
        "Wrote onboarding documentation for teammates.",
    ]

    result = find_skill_evidence("fastapi", evidence, fallback_skill_name="api")

    assert result == "Built REST services and API endpoints for internal tools."
