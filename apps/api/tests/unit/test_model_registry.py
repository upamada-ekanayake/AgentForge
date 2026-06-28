import pytest

from app.services.model_registry import (
    ModelRegistryError,
    get_model_task_config,
    list_model_task_configs,
)


def test_get_enabled_model_task_config_returns_reasoning_model() -> None:
    config = get_model_task_config("internship_reasoning")

    assert config.task_name == "internship_reasoning"
    assert config.provider == "ollama"
    assert config.model
    assert config.supports_json is True
    assert config.enabled is True


def test_output_validation_uses_deterministic_low_temperature() -> None:
    config = get_model_task_config("output_validation")

    assert config.task_name == "output_validation"
    assert config.temperature == 0.0
    assert config.supports_json is True


def test_disabled_model_task_raises_clear_error() -> None:
    with pytest.raises(ModelRegistryError, match="disabled"):
        get_model_task_config("cover_letter")


def test_unknown_model_task_raises_clear_error() -> None:
    with pytest.raises(ModelRegistryError, match="not registered"):
        get_model_task_config("unknown_task")


def test_list_model_task_configs_includes_disabled_by_default() -> None:
    configs = list_model_task_configs()
    task_names = {config.task_name for config in configs}

    assert {"internship_reasoning", "cover_letter", "interview_prep"}.issubset(
        task_names,
    )


def test_list_model_task_configs_can_filter_disabled_tasks() -> None:
    configs = list_model_task_configs(include_disabled=False)

    assert configs
    assert all(config.enabled for config in configs)
    assert {config.task_name for config in configs} == {
        "internship_reasoning",
        "output_validation",
    }
