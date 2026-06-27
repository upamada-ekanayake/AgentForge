from collections.abc import Callable

from app.agents.planner_agent import plan_task
from app.modules.agents.schemas import (
    PlannerInput,
    PlannerOutputFormat,
    PlannerTaskType,
)


def test_compare_query_returns_internship_match_plan(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies comparison intent maps to the CV-to-internship match workflow.
    plan = plan_task(
        make_planner_input(
            "Compare my CV with this backend internship and identify gaps.",
        ),
    )

    assert plan.task_type == PlannerTaskType.COMPARE_CV_TO_INTERNSHIP
    assert plan.output_format == PlannerOutputFormat.INTERNSHIP_MATCH_REPORT
    assert plan.required_context == ["cv", "internship_post"]
    assert plan.needs_clarification is False
    assert plan.clarifying_question is None
    assert "retrieve_cv_chunks" in plan.steps
    assert "generate_recommendations" in plan.steps


def test_cover_letter_query_returns_cover_letter_plan(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies cover-letter intent does not accidentally enter match scoring.
    plan = plan_task(
        make_planner_input("Write a cover letter so I can apply for this role."),
    )

    assert plan.task_type == PlannerTaskType.GENERATE_COVER_LETTER
    assert plan.output_format == PlannerOutputFormat.COVER_LETTER_DRAFT
    assert plan.required_context == ["cv", "internship_post"]
    assert plan.needs_clarification is False
    assert "draft_cover_letter" in plan.steps


def test_interview_query_returns_interview_preparation_plan(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies interview-preparation intent produces the interview guide plan.
    plan = plan_task(
        make_planner_input("Prepare interview questions for this internship."),
    )

    assert plan.task_type == PlannerTaskType.PREPARE_INTERVIEW_QUESTIONS
    assert plan.output_format == PlannerOutputFormat.INTERVIEW_PREP_GUIDE
    assert plan.required_context == ["cv", "internship_post"]
    assert plan.needs_clarification is False
    assert "generate_interview_questions" in plan.steps


def test_unknown_query_requests_clarification(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies unclear intent stops safely instead of guessing a workflow.
    plan = plan_task(make_planner_input("Can you help me with this?"))

    assert plan.task_type == PlannerTaskType.UNKNOWN
    assert plan.confidence == 0.35
    assert plan.required_context == []
    assert plan.steps == []
    assert plan.output_format is None
    assert plan.needs_clarification is True
    assert plan.clarifying_question is not None
    assert "compare your CV" in plan.clarifying_question
    assert "cover letter" in plan.clarifying_question
    assert "interview questions" in plan.clarifying_question


def test_known_planner_confidence_values_are_high_and_bounded(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies recognized intents stay within valid high-confidence ranges.
    queries = [
        "Match my CV to this internship.",
        "Generate a cover letter for this company.",
        "Prepare me for interview questions.",
    ]

    for query in queries:
        plan = plan_task(make_planner_input(query))
        assert 0.8 <= plan.confidence <= 1.0
        assert plan.needs_clarification is False


def test_unknown_planner_confidence_is_low_and_bounded(
    make_planner_input: Callable[[str], PlannerInput],
) -> None:
    # Verifies unclear intent remains low confidence but still schema-valid.
    plan = plan_task(make_planner_input("Tell me something useful."))

    assert 0.0 <= plan.confidence < 0.5
    assert plan.needs_clarification is True
