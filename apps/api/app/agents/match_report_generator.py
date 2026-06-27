from app.agents.skill_graph import (
    align_skills,
    calculate_weighted_score,
    detect_skills,
    find_skill_evidence,
    get_skill_category,
)
from app.modules.agents.schemas import (
    MatchReportInput,
    MatchReportOutput,
    SkillGap,
    SkillMatch,
)


def generate_match_report(report_input: MatchReportInput) -> MatchReportOutput:
    cv_text = " ".join(report_input.cv_evidence)
    internship_text = " ".join(
        [
            report_input.internship_summary.description,
            report_input.internship_summary.requirements or "",
        ],
    )

    cv_skills = detect_skills(cv_text)
    required_skills = detect_skills(internship_text)
    skill_alignments, missing_skills = align_skills(required_skills, cv_skills)

    match_score = calculate_weighted_score(required_skills, skill_alignments)
    matched_skills = [
        SkillMatch(
            skill=alignment.required_skill,
            category=alignment.category,
            match_type=alignment.match_type,
            confidence=alignment.confidence,
            evidence=find_skill_evidence(
                alignment.required_skill,
                report_input.cv_evidence,
                alignment.cv_skill,
            ),
        )
        for alignment in sorted(
            skill_alignments,
            key=lambda item: (item.category, item.required_skill),
        )
    ]
    missing_skills = [
        SkillGap(
            skill=skill.name,
            category=skill.category,
            recommendation=_recommendation_for_skill(skill.name),
        )
        for skill in sorted(missing_skills, key=lambda item: (item.category, item.name))
    ]
    missing_skill_names = [skill.skill for skill in missing_skills]
    recommendations = _build_recommendations(
        match_score,
        missing_skill_names,
        has_related_matches=any(skill.match_type == "related" for skill in matched_skills),
    )

    return MatchReportOutput(
        match_score=match_score,
        summary=_build_summary(
            match_score,
            matched_skills,
            missing_skill_names,
            required_skill_count=len(required_skills),
        ),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        recommendations=recommendations,
        source_chunk_ids=report_input.source_chunk_ids,
    )


def _recommendation_for_skill(skill: str) -> str:
    category = get_skill_category(skill)
    return (
        f"Add stronger {category} evidence for {skill} through a project, "
        "bullet point, or measurable achievement."
    )


def _build_recommendations(
    match_score: float,
    missing_skills: list[str],
    has_related_matches: bool,
) -> list[str]:
    recommendations: list[str] = []
    if missing_skills:
        recommendations.append(
            "Prioritize the missing skills that appear in the internship requirements.",
        )
        recommendations.extend(
            _recommendation_for_skill(skill) for skill in missing_skills[:3]
        )
    else:
        recommendations.append(
            "The skill graph found coverage for all detected internship skills.",
        )

    if has_related_matches:
        recommendations.append(
            "Some matches are related-skill matches; make the connection explicit in the CV.",
        )

    if match_score < 50:
        recommendations.append(
            "Strengthen the CV with role-specific project evidence before applying.",
        )
    elif match_score < 80:
        recommendations.append(
            "Add more specific examples to improve alignment with the internship.",
        )
    else:
        recommendations.append(
            "Use the strongest matched skills prominently in the application.",
        )

    return recommendations


def _build_summary(
    match_score: float,
    matched_skills: list[SkillMatch],
    missing_skills: list[str],
    required_skill_count: int,
) -> str:
    direct_matches = sorted(
        skill.skill for skill in matched_skills if skill.match_type == "direct"
    )
    related_matches = sorted(
        skill.skill for skill in matched_skills if skill.match_type == "related"
    )
    matched_text = ", ".join(direct_matches + related_matches) if matched_skills else "none"
    missing_text = ", ".join(missing_skills) if missing_skills else "none"
    return (
        f"Skill graph match score is {match_score:.2f}% across "
        f"{required_skill_count} detected internship skills. "
        f"Matched skills: {matched_text}. Missing skills: {missing_text}."
    )
