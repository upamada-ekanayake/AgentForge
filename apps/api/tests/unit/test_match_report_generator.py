import uuid
from collections.abc import Callable

from app.agents.match_report_generator import generate_match_report
from app.modules.agents.schemas import MatchReportInput


def test_generates_match_report_with_matched_skills(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies direct CV evidence produces matched skills in the report.
    report = generate_match_report(
        make_match_report_input(
            ["Built FastAPI APIs with PostgreSQL, SQL, Git, and Docker."],
            "Build backend API services.",
            "FastAPI PostgreSQL Docker Git",
        ),
    )

    assert report.match_score == 100.0
    assert [skill.skill for skill in report.matched_skills] == [
        "api",
        "fastapi",
        "postgresql",
        "docker",
        "git",
    ]
    assert all(skill.match_type == "direct" for skill in report.matched_skills)


def test_detects_missing_skills(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies required skills without direct or related CV evidence become gaps.
    report = generate_match_report(
        make_match_report_input(
            ["Built REST services with SQL."],
            "Build backend services.",
            "FastAPI PostgreSQL Docker",
        ),
    )

    assert [skill.skill for skill in report.missing_skills] == ["docker"]
    assert report.missing_skills[0].category == "infrastructure"


def test_calculates_match_score_correctly(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies weighted score combines direct, related, and missing skill weights.
    report = generate_match_report(
        make_match_report_input(
            ["Built REST services with SQL."],
            "Build backend services.",
            "FastAPI PostgreSQL Docker",
        ),
    )

    assert report.match_score == 68.14


def test_produces_recommendations_for_missing_skills(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies missing skills generate specific improvement guidance.
    report = generate_match_report(
        make_match_report_input(
            ["Built REST services with SQL."],
            "Build backend services.",
            "FastAPI PostgreSQL Docker",
        ),
    )

    assert (
        "Prioritize the missing skills that appear in the internship requirements."
        in report.recommendations
    )
    assert any("docker" in recommendation for recommendation in report.recommendations)


def test_includes_source_chunk_ids(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies source chunk IDs survive report generation for traceability.
    source_chunk_ids = [
        uuid.UUID("10000000-0000-0000-0000-000000000201"),
        uuid.UUID("10000000-0000-0000-0000-000000000202"),
    ]

    report = generate_match_report(
        make_match_report_input(
            ["Built FastAPI APIs with PostgreSQL."],
            "Build backend APIs.",
            "FastAPI PostgreSQL",
            source_chunk_ids,
        ),
    )

    assert report.source_chunk_ids == source_chunk_ids


def test_handles_no_detected_internship_skills_safely(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies generic internship text does not crash or invent requirements.
    report = generate_match_report(
        make_match_report_input(
            ["Built FastAPI APIs with PostgreSQL."],
            "Friendly workplace with mentoring.",
            None,
        ),
    )

    assert report.match_score == 0.0
    assert report.matched_skills == []
    assert report.missing_skills == []
    assert "0 detected internship skills" in report.summary


def test_uses_skill_graph_related_matching(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies related skill matches are surfaced with lower confidence.
    report = generate_match_report(
        make_match_report_input(
            ["Built REST services with SQL."],
            "Build backend services.",
            "FastAPI PostgreSQL",
        ),
    )

    related_matches = {
        skill.skill: skill
        for skill in report.matched_skills
        if skill.match_type == "related"
    }
    assert related_matches["fastapi"].confidence == 0.9
    assert related_matches["postgresql"].confidence == 0.85
    assert related_matches["fastapi"].evidence == "Built REST services with SQL."
    assert any("related-skill matches" in item for item in report.recommendations)


def test_summary_includes_score_and_matched_missing_skills(
    make_match_report_input: Callable[
        [list[str], str, str | None, list[uuid.UUID] | None],
        MatchReportInput,
    ],
) -> None:
    # Verifies summary is useful for UI and reviewer output.
    report = generate_match_report(
        make_match_report_input(
            ["Built REST services with SQL."],
            "Build backend services.",
            "FastAPI PostgreSQL Docker",
        ),
    )

    assert "Skill graph match score is 68.14%" in report.summary
    assert "Matched skills: backend development, fastapi, postgresql." in report.summary
    assert "Missing skills: docker." in report.summary
