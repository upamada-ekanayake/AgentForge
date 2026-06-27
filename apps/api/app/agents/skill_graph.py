import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillNode:
    name: str
    category: str
    weight: float
    aliases: tuple[str, ...]
    related: dict[str, float]


@dataclass(frozen=True)
class DetectedSkill:
    name: str
    category: str
    weight: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class SkillAlignment:
    required_skill: str
    category: str
    confidence: float
    match_type: str
    cv_skill: str | None


SKILL_GRAPH: dict[str, SkillNode] = {
    "python": SkillNode(
        name="python",
        category="backend",
        weight=1.4,
        aliases=("python", "python programming"),
        related={"fastapi": 0.75, "django": 0.65, "flask": 0.65, "backend development": 0.65},
    ),
    "fastapi": SkillNode(
        name="fastapi",
        category="backend",
        weight=1.5,
        aliases=("fastapi", "fast api"),
        related={"python": 0.75, "api": 0.9, "backend development": 0.85},
    ),
    "django": SkillNode(
        name="django",
        category="backend",
        weight=1.1,
        aliases=("django",),
        related={"python": 0.65, "api": 0.65, "backend development": 0.75},
    ),
    "flask": SkillNode(
        name="flask",
        category="backend",
        weight=1.1,
        aliases=("flask",),
        related={"python": 0.65, "api": 0.65, "backend development": 0.75},
    ),
    "api": SkillNode(
        name="api",
        category="backend",
        weight=1.0,
        aliases=(
            "api",
            "apis",
            "rest api",
            "rest apis",
            "restful api",
            "restful apis",
            "api development",
            "backend api",
            "backend apis",
            "rest services",
            "http services",
        ),
        related={"fastapi": 0.9, "backend development": 0.85, "django": 0.65, "flask": 0.65},
    ),
    "backend development": SkillNode(
        name="backend development",
        category="backend",
        weight=1.2,
        aliases=(
            "backend development",
            "back end development",
            "backend engineering",
            "backend services",
            "server side",
            "server-side",
        ),
        related={"api": 0.85, "fastapi": 0.85, "python": 0.65, "docker": 0.55},
    ),
    "postgresql": SkillNode(
        name="postgresql",
        category="database",
        weight=1.3,
        aliases=("postgresql", "postgres"),
        related={"sql": 0.85, "database": 0.75},
    ),
    "sql": SkillNode(
        name="sql",
        category="database",
        weight=1.0,
        aliases=("sql", "relational database", "relational databases"),
        related={"postgresql": 0.85, "database": 0.75},
    ),
    "database": SkillNode(
        name="database",
        category="database",
        weight=0.9,
        aliases=("database", "databases", "data model", "data models"),
        related={"sql": 0.75, "postgresql": 0.75},
    ),
    "docker": SkillNode(
        name="docker",
        category="infrastructure",
        weight=1.1,
        aliases=("docker", "container", "containers", "containerized", "containerised"),
        related={"backend development": 0.55},
    ),
    "git": SkillNode(
        name="git",
        category="tooling",
        weight=0.8,
        aliases=("git", "github", "version control"),
        related={},
    ),
    "machine learning": SkillNode(
        name="machine learning",
        category="ai",
        weight=1.3,
        aliases=("machine learning", "ml"),
        related={"ai": 0.8, "embeddings": 0.6},
    ),
    "ai": SkillNode(
        name="ai",
        category="ai",
        weight=1.1,
        aliases=("ai", "artificial intelligence"),
        related={"machine learning": 0.8, "rag": 0.65},
    ),
    "embeddings": SkillNode(
        name="embeddings",
        category="ai",
        weight=1.2,
        aliases=("embedding", "embeddings", "vector embedding", "vector embeddings"),
        related={"rag": 0.8, "qdrant": 0.7, "machine learning": 0.6},
    ),
    "qdrant": SkillNode(
        name="qdrant",
        category="ai",
        weight=1.1,
        aliases=("qdrant", "vector database", "vector db"),
        related={"embeddings": 0.7, "rag": 0.75},
    ),
    "rag": SkillNode(
        name="rag",
        category="ai",
        weight=1.4,
        aliases=("rag", "retrieval augmented generation", "retrieval-augmented generation"),
        related={"embeddings": 0.8, "qdrant": 0.75, "ai": 0.65},
    ),
    "writing": SkillNode(
        name="writing",
        category="communication",
        weight=0.8,
        aliases=("writing", "written communication", "documentation", "copywriting"),
        related={"communication": 0.8},
    ),
    "product thinking": SkillNode(
        name="product thinking",
        category="product",
        weight=1.0,
        aliases=("product thinking", "product sense", "user research", "user-focused"),
        related={"communication": 0.55, "writing": 0.55},
    ),
    "communication": SkillNode(
        name="communication",
        category="communication",
        weight=0.9,
        aliases=("communication", "communicate", "collaboration", "stakeholder"),
        related={"writing": 0.8, "product thinking": 0.55},
    ),
}


def detect_skills(text: str) -> dict[str, DetectedSkill]:
    normalized_text = _normalize(text)
    detected: dict[str, DetectedSkill] = {}

    for skill_name, skill in SKILL_GRAPH.items():
        matched_terms = tuple(
            term
            for term in (skill.name, *skill.aliases)
            if _contains_term(normalized_text, term)
        )
        if matched_terms:
            detected[skill_name] = DetectedSkill(
                name=skill.name,
                category=skill.category,
                weight=skill.weight,
                matched_terms=matched_terms,
            )

    return detected


def align_skills(
    required_skills: dict[str, DetectedSkill],
    cv_skills: dict[str, DetectedSkill],
) -> tuple[list[SkillAlignment], list[DetectedSkill]]:
    matched: list[SkillAlignment] = []
    missing: list[DetectedSkill] = []

    for required_name, required_skill in required_skills.items():
        if required_name in cv_skills:
            matched.append(
                SkillAlignment(
                    required_skill=required_name,
                    category=required_skill.category,
                    confidence=1.0,
                    match_type="direct",
                    cv_skill=required_name,
                ),
            )
            continue

        related_match = _best_related_match(required_name, cv_skills)
        if related_match is not None:
            cv_skill, confidence = related_match
            matched.append(
                SkillAlignment(
                    required_skill=required_name,
                    category=required_skill.category,
                    confidence=confidence,
                    match_type="related",
                    cv_skill=cv_skill,
                ),
            )
            continue

        missing.append(required_skill)

    return matched, missing


def calculate_weighted_score(
    required_skills: dict[str, DetectedSkill],
    alignments: list[SkillAlignment],
) -> float:
    total_weight = sum(skill.weight for skill in required_skills.values())
    if total_weight == 0:
        return 0.0

    earned_weight = sum(
        required_skills[alignment.required_skill].weight * alignment.confidence
        for alignment in alignments
    )
    return round((earned_weight / total_weight) * 100, 2)


def find_skill_evidence(
    skill_name: str,
    cv_evidence: list[str],
    fallback_skill_name: str | None = None,
) -> str:
    for candidate_skill in (skill_name, fallback_skill_name):
        if candidate_skill is None:
            continue
        for evidence in cv_evidence:
            if _contains_any_skill_term(evidence, candidate_skill):
                return evidence

    return "Skill alignment is inferred from related CV evidence."


def get_skill_category(skill_name: str) -> str:
    return SKILL_GRAPH[skill_name].category


def _best_related_match(
    required_name: str,
    cv_skills: dict[str, DetectedSkill],
) -> tuple[str, float] | None:
    required_node = SKILL_GRAPH[required_name]
    candidates: list[tuple[str, float]] = []

    for cv_name in cv_skills:
        cv_node = SKILL_GRAPH[cv_name]
        confidence = max(
            required_node.related.get(cv_name, 0.0),
            cv_node.related.get(required_name, 0.0),
        )
        if confidence >= 0.6:
            candidates.append((cv_name, confidence))

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: candidate[1])


def _contains_any_skill_term(text: str, skill_name: str) -> bool:
    normalized_text = _normalize(text)
    skill = SKILL_GRAPH[skill_name]
    return any(
        _contains_term(normalized_text, term)
        for term in (skill.name, *skill.aliases)
    )


def _contains_term(normalized_text: str, term: str) -> bool:
    normalized_term = _normalize(term)
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_term) + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text) is not None


def _normalize(text: str) -> str:
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()
