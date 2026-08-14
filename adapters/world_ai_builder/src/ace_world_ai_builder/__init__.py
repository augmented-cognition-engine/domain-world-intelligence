"""Trusted World AI Builder application adapter.

Journey strategies remain importable against the released Core used by the
inert World pack. Executor exports load only when a host discovers this trusted
application distribution and therefore requires the newer public build seam.
"""

from __future__ import annotations

from importlib import import_module

from .journey import (
    DEFAULT_WORLD_AI_BUILDER_PLAN,
    SUPPORTED_RECORDED_SOURCE_OPTION_IDS,
    AuthorizedWorldBuilderEffectsAuthority,
    WorldAIBuilderPlan,
    run_world_ai_builder_journey,
)

_EXECUTOR_EXPORTS = frozenset(
    {
        "READ_KINDS",
        "RECORDED_JOURNEY_STARTED_AT",
        "SUPPORTED_RECORDED_SOURCE_GROUP_IDS",
        "WORLD_AI_PROFILE_ID",
        "WorldAIBuilderEnvironment",
        "WorldAIBuilderExecutor",
        "WorldAIBuilderExecutorError",
        "load_recorded_world_ai_admission_materials",
        "load_recorded_world_ai_source_materials",
        "load_world_ai_onboarding_profile",
        "plan_from_authorized_build",
    }
)


def __getattr__(name: str):
    if name not in _EXECUTOR_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(".executor", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | _EXECUTOR_EXPORTS)


__all__ = [
    "DEFAULT_WORLD_AI_BUILDER_PLAN",
    "READ_KINDS",
    "RECORDED_JOURNEY_STARTED_AT",
    "SUPPORTED_RECORDED_SOURCE_GROUP_IDS",
    "SUPPORTED_RECORDED_SOURCE_OPTION_IDS",
    "WORLD_AI_PROFILE_ID",
    "AuthorizedWorldBuilderEffectsAuthority",
    "WorldAIBuilderEnvironment",
    "WorldAIBuilderExecutor",
    "WorldAIBuilderExecutorError",
    "WorldAIBuilderPlan",
    "load_recorded_world_ai_admission_materials",
    "load_recorded_world_ai_source_materials",
    "load_world_ai_onboarding_profile",
    "plan_from_authorized_build",
    "run_world_ai_builder_journey",
]
