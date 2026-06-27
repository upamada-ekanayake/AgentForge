from app.modules.agents.schemas import (
    PlannerInput,
    PlannerOutput,
    PlannerOutputFormat,
    PlannerTaskType,
)


COMPARE_KEYWORDS = {"compare", "match", "fit", "improve", "gap"}
COVER_LETTER_KEYWORDS = {"cover letter", "letter", "apply"}
INTERVIEW_KEYWORDS = {"interview", "questions", "prepare"}


def plan_task(planner_input: PlannerInput) -> PlannerOutput:
    query = planner_input.user_query.lower()

    if _contains_keyword(query, COMPARE_KEYWORDS):
        return PlannerOutput(
            task_type=PlannerTaskType.COMPARE_CV_TO_INTERNSHIP,
            confidence=0.9,
            required_context=["cv", "internship_post"],
            steps=[
                "retrieve_cv_chunks",
                "load_internship_post",
                "compare_skills",
                "identify_gaps",
                "generate_recommendations",
            ],
            output_format=PlannerOutputFormat.INTERNSHIP_MATCH_REPORT,
            needs_clarification=False,
            clarifying_question=None,
        )

    if _contains_keyword(query, COVER_LETTER_KEYWORDS):
        return PlannerOutput(
            task_type=PlannerTaskType.GENERATE_COVER_LETTER,
            confidence=0.88,
            required_context=["cv", "internship_post"],
            steps=[
                "retrieve_cv_chunks",
                "load_internship_post",
                "identify_relevant_experience",
                "draft_cover_letter",
            ],
            output_format=PlannerOutputFormat.COVER_LETTER_DRAFT,
            needs_clarification=False,
            clarifying_question=None,
        )

    if _contains_keyword(query, INTERVIEW_KEYWORDS):
        return PlannerOutput(
            task_type=PlannerTaskType.PREPARE_INTERVIEW_QUESTIONS,
            confidence=0.88,
            required_context=["cv", "internship_post"],
            steps=[
                "retrieve_cv_chunks",
                "load_internship_post",
                "identify_role_requirements",
                "generate_interview_questions",
                "suggest_preparation_notes",
            ],
            output_format=PlannerOutputFormat.INTERVIEW_PREP_GUIDE,
            needs_clarification=False,
            clarifying_question=None,
        )

    return PlannerOutput(
        task_type=PlannerTaskType.UNKNOWN,
        confidence=0.35,
        required_context=[],
        steps=[],
        output_format=None,
        needs_clarification=True,
        clarifying_question=(
            "Do you want me to compare your CV, generate a cover letter, "
            "or prepare interview questions?"
        ),
    )


def _contains_keyword(query: str, keywords: set[str]) -> bool:
    return any(keyword in query for keyword in keywords)
