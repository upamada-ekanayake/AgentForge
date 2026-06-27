import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import ROOT_DIR


PROMPTS_DIR = ROOT_DIR / "packages" / "prompts"
PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


class PromptRegistryError(RuntimeError):
    """Raised when a prompt template cannot be loaded or rendered."""


@dataclass(frozen=True)
class PromptTemplate:
    prompt_name: str
    prompt_version: str
    body: str


@dataclass(frozen=True)
class RenderedPrompt:
    prompt_name: str
    prompt_version: str
    content: str


def load_prompt_template(
    prompt_name: str,
    prompt_version: str,
) -> PromptTemplate:
    path = PROMPTS_DIR / f"{prompt_name}_{prompt_version}.md"
    if not path.is_file():
        raise PromptRegistryError(
            f"Prompt template not found: {prompt_name}_{prompt_version}.md",
        )

    raw_template = path.read_text(encoding="utf-8")
    metadata, body = _parse_front_matter(raw_template)
    template_name = metadata.get("prompt_name")
    template_version = metadata.get("prompt_version")

    if template_name != prompt_name or template_version != prompt_version:
        raise PromptRegistryError(
            "Prompt metadata does not match the requested name and version.",
        )

    return PromptTemplate(
        prompt_name=template_name,
        prompt_version=template_version,
        body=body.strip(),
    )


def render_prompt_template(
    prompt_name: str,
    prompt_version: str,
    variables: dict[str, str],
) -> RenderedPrompt:
    template = load_prompt_template(prompt_name, prompt_version)
    missing_variables = sorted(
        {
            match.group(1)
            for match in PLACEHOLDER_PATTERN.finditer(template.body)
            if match.group(1) not in variables
        },
    )
    if missing_variables:
        raise PromptRegistryError(
            f"Missing prompt variable(s): {', '.join(missing_variables)}",
        )

    def replace_placeholder(match: re.Match[str]) -> str:
        return variables[match.group(1)]

    return RenderedPrompt(
        prompt_name=template.prompt_name,
        prompt_version=template.prompt_version,
        content=PLACEHOLDER_PATTERN.sub(replace_placeholder, template.body),
    )


def _parse_front_matter(raw_template: str) -> tuple[dict[str, str], str]:
    if not raw_template.startswith("---"):
        raise PromptRegistryError("Prompt template is missing metadata header.")

    parts = raw_template.split("---", 2)
    if len(parts) != 3:
        raise PromptRegistryError("Prompt template metadata header is invalid.")

    metadata_lines = parts[1].strip().splitlines()
    metadata: dict[str, str] = {}
    for line in metadata_lines:
        key, separator, value = line.partition(":")
        if not separator:
            raise PromptRegistryError(f"Invalid prompt metadata line: {line}")
        metadata[key.strip()] = value.strip()

    return metadata, parts[2]
