from collections.abc import Callable

from app.agents.output_validator import validate_reasoner_output
from app.modules.agents.schemas import (
    LLMReasonerOutput,
    MatchReportOutput,
    OutputValidationInput,
    RetrievalQuality,
    RetrievalQualityLevel,
    SkillGap,
    ValidationSeverity,
)


def test_large_score_disagreement_warning(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies large deterministic-vs-LLM score disagreement is flagged.
    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(match_score=70.0),
            make_llm_reasoning(),
            llm_match_score=90.5,
        ),
    )

    assert validation.score_delta == 20.5
    assert validation.findings[0].code == "large_score_disagreement"
    assert validation.findings[0].severity == ValidationSeverity.WARNING


def test_high_confidence_with_weak_retrieval_warning(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_retrieval_quality: Callable[[RetrievalQualityLevel, str | None], RetrievalQuality],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies high LLM confidence is risky when retrieval quality is weak.
    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(),
            make_llm_reasoning(confidence=0.9, risk_flags=["weak retrieval noted"]),
            make_retrieval_quality(RetrievalQualityLevel.WEAK),
        ),
    )

    assert [finding.code for finding in validation.findings] == [
        "high_confidence_with_weak_retrieval",
    ]
    assert validation.findings[0].severity == ValidationSeverity.WARNING


def test_missing_retrieval_risk_flag_detection(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_retrieval_quality: Callable[[RetrievalQualityLevel, str | None], RetrievalQuality],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies retrieval warnings must be reflected in LLM risk flags.
    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(),
            make_llm_reasoning(risk_flags=[]),
            make_retrieval_quality(
                RetrievalQualityLevel.WEAK,
                "Retrieved CV evidence may be weak.",
            ),
        ),
    )

    assert "missing_retrieval_risk_flag" in [
        finding.code for finding in validation.findings
    ]
    assert next(
        finding
        for finding in validation.findings
        if finding.code == "missing_retrieval_risk_flag"
    ).severity == ValidationSeverity.INFO


def test_missing_skill_not_discussed_detection(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies deterministic missing skills should appear in LLM weaknesses.
    missing_skills = [
        SkillGap(skill="docker", recommendation="Add Docker project evidence."),
    ]

    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(missing_skills=missing_skills),
            make_llm_reasoning(weaknesses=["Needs stronger API examples."]),
        ),
    )

    assert validation.findings[0].code == "missing_skill_not_discussed"
    assert validation.findings[0].details == {"skills": ["docker"]}
    assert validation.findings[0].severity == ValidationSeverity.INFO


def test_multiple_warnings_returned_together(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_retrieval_quality: Callable[[RetrievalQualityLevel, str | None], RetrievalQuality],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies independent validation findings can be returned in one response.
    missing_skills = [
        SkillGap(skill="docker", recommendation="Add Docker project evidence."),
    ]

    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(match_score=70.0, missing_skills=missing_skills),
            make_llm_reasoning(confidence=0.95, weaknesses=[], risk_flags=[]),
            make_retrieval_quality(
                RetrievalQualityLevel.WEAK,
                "Retrieved CV evidence may be weak.",
            ),
            llm_match_score=95.0,
        ),
    )

    assert [finding.code for finding in validation.findings] == [
        "large_score_disagreement",
        "high_confidence_with_weak_retrieval",
        "missing_retrieval_risk_flag",
        "missing_skill_not_discussed",
    ]


def test_clean_validation_with_no_warnings(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_retrieval_quality: Callable[[RetrievalQualityLevel, str | None], RetrievalQuality],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies aligned deterministic and LLM outputs produce no findings.
    missing_skills = [
        SkillGap(skill="docker", recommendation="Add Docker project evidence."),
    ]

    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(match_score=82.0, missing_skills=missing_skills),
            make_llm_reasoning(
                confidence=0.7,
                weaknesses=["Docker evidence could be stronger."],
                risk_flags=["Retrieval quality reviewed."],
            ),
            make_retrieval_quality(RetrievalQualityLevel.MEDIUM),
            llm_match_score=85.0,
        ),
    )

    assert validation.is_valid is True
    assert validation.score_delta == 3.0
    assert validation.findings == []


def test_severity_levels_are_assigned_correctly(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_retrieval_quality: Callable[[RetrievalQualityLevel, str | None], RetrievalQuality],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies current validator rules use warning/info severities, not errors.
    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(match_score=60.0),
            make_llm_reasoning(confidence=0.95, risk_flags=[]),
            make_retrieval_quality(
                RetrievalQualityLevel.WEAK,
                "Retrieved CV evidence may be weak.",
            ),
            llm_match_score=95.0,
        ),
    )

    severities = {finding.code: finding.severity for finding in validation.findings}
    assert severities["large_score_disagreement"] == ValidationSeverity.WARNING
    assert severities["high_confidence_with_weak_retrieval"] == ValidationSeverity.WARNING
    assert severities["missing_retrieval_risk_flag"] == ValidationSeverity.INFO
    assert validation.is_valid is True


def test_validator_handles_empty_risk_flags_safely(
    make_match_report_output: Callable[[float, list[SkillGap] | None], MatchReportOutput],
    make_llm_reasoning: Callable[[float, list[str] | None, list[str] | None], LLMReasonerOutput],
    make_output_validation_input: Callable[
        [MatchReportOutput, LLMReasonerOutput, RetrievalQuality | None, float | None],
        OutputValidationInput,
    ],
) -> None:
    # Verifies empty risk flags are safe when there is no retrieval warning.
    validation = validate_reasoner_output(
        make_output_validation_input(
            make_match_report_output(),
            make_llm_reasoning(risk_flags=[]),
            retrieval_quality=None,
        ),
    )

    assert validation.is_valid is True
    assert validation.findings == []
