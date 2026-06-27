from app.modules.agents.schemas import (
    OutputValidationFinding,
    OutputValidationInput,
    OutputValidationOutput,
    ValidationSeverity,
)


LARGE_SCORE_DISAGREEMENT_THRESHOLD = 10.0
HIGH_CONFIDENCE_THRESHOLD = 0.85


def validate_reasoner_output(
    validation_input: OutputValidationInput,
) -> OutputValidationOutput:
    findings: list[OutputValidationFinding] = []
    deterministic_score = validation_input.deterministic_report.match_score
    llm_score = validation_input.llm_match_score
    score_delta = None

    if llm_score is not None:
        score_delta = round(abs(deterministic_score - llm_score), 2)
        if score_delta > LARGE_SCORE_DISAGREEMENT_THRESHOLD:
            findings.append(
                OutputValidationFinding(
                    code="large_score_disagreement",
                    severity=ValidationSeverity.WARNING,
                    message=(
                        "Large disagreement detected between deterministic "
                        "match score and LLM score."
                    ),
                    details={
                        "deterministic_score": deterministic_score,
                        "llm_score": llm_score,
                        "difference": score_delta,
                    },
                ),
            )

    if (
        validation_input.retrieval_quality is not None
        and validation_input.retrieval_quality.quality_level == "weak"
        and validation_input.llm_reasoning.confidence >= HIGH_CONFIDENCE_THRESHOLD
    ):
        findings.append(
            OutputValidationFinding(
                code="high_confidence_with_weak_retrieval",
                severity=ValidationSeverity.WARNING,
                message="LLM confidence is high even though retrieval quality is weak.",
                details={
                    "confidence": validation_input.llm_reasoning.confidence,
                    "quality_level": validation_input.retrieval_quality.quality_level,
                },
            ),
        )

    if (
        validation_input.retrieval_quality is not None
        and validation_input.retrieval_quality.warning
        and not validation_input.llm_reasoning.risk_flags
    ):
        findings.append(
            OutputValidationFinding(
                code="missing_retrieval_risk_flag",
                severity=ValidationSeverity.INFO,
                message="Retrieval warning exists, but LLM output has no risk flags.",
                details={"warning": validation_input.retrieval_quality.warning},
            ),
        )

    missing_skill_names = [
        gap.skill.lower()
        for gap in validation_input.deterministic_report.missing_skills
    ]
    weakness_text = " ".join(validation_input.llm_reasoning.weaknesses).lower()
    uncovered_missing_skills = [
        skill for skill in missing_skill_names if skill not in weakness_text
    ]
    if uncovered_missing_skills:
        findings.append(
            OutputValidationFinding(
                code="missing_skill_not_discussed",
                severity=ValidationSeverity.INFO,
                message="Some deterministic missing skills are not discussed as weaknesses.",
                details={"skills": uncovered_missing_skills},
            ),
        )

    return OutputValidationOutput(
        is_valid=not any(
            finding.severity == ValidationSeverity.ERROR for finding in findings
        ),
        deterministic_score=deterministic_score,
        llm_score=llm_score,
        score_delta=score_delta,
        findings=findings,
    )
