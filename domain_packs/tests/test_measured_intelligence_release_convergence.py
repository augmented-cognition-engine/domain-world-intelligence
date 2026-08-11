from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest


def _require_candidate_contracts() -> None:
    if importlib.util.find_spec("ace.application.measured_impact") is None:
        pytest.skip("release convergence requires the stacked Core measured-impact candidate")
    if importlib.util.find_spec("ace_reference_workspace_action") is None:
        pytest.skip("release convergence requires the separately packaged Core action adapter")


def test_artifact_identity_is_exact_and_content_derived(tmp_path: Path) -> None:
    _require_candidate_contracts()
    from scripts.measured_intelligence_release_convergence import artifact_identity

    candidate = tmp_path / "candidate.whl"
    candidate.write_bytes(b"candidate-artifact")

    assert artifact_identity(candidate) == {
        "filename": "candidate.whl",
        "sha256": "sha256:75ec5f680183fbca988b8bd9f3090f00d31dbf34792a50cd7e66763d994ab083",
    }


def test_core_checkout_runtime_is_rejected(tmp_path: Path) -> None:
    _require_candidate_contracts()
    from scripts.measured_intelligence_release_convergence import (
        validate_core_runtime_outside_checkouts,
    )

    checkout = tmp_path / "core"
    module = checkout / "ace" / "__init__.py"
    module.parent.mkdir(parents=True)
    module.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="requires the built Core artifact"):
        validate_core_runtime_outside_checkouts(module_path=module, forbidden_roots=(checkout,))


@pytest.mark.asyncio
async def test_public_projection_freezes_the_bounded_measured_result(tmp_path: Path) -> None:
    _require_candidate_contracts()
    from scripts.measured_intelligence_release_convergence import build_public_projection
    from scripts.p2c10_independent_correction_reproduction import (
        run_independent_correction_reproduction,
    )

    result = await run_independent_correction_reproduction(tmp_path)
    coordinate = {"filename": "candidate.whl", "sha256": "sha256:" + "a" * 64}
    projection = build_public_projection(
        result,
        core_commit="a" * 40,
        world_commit="b" * 40,
        core_wheel=coordinate,
        action_adapter_wheel=coordinate,
        world_wheel=coordinate,
        core_distribution_version="0.5.0",
        action_adapter_distribution_version="0.1.0",
        world_distribution_version="0.9.0",
    )

    assert projection["measured_result"] == {
        "classification": "useful",
        "matched_pair_count": 2,
        "mean_effect": 1.0,
        "uncertainty": None,
        "limitations": result["evaluation"]["limitations"],
    }
    assert projection["governed_feedback"] == {
        "proposed_action": "promote",
        "live_effect": False,
        "selectable": False,
        "requires_human_review": True,
        "applied": False,
        "historical_replay": True,
        "replay_reauthorized": False,
    }
    assert projection["claim_boundary"]["ace_0_6_complete"] is False

    effective = copy.deepcopy(result)
    effective["proposal"]["live_effect"] = True
    with pytest.raises(AssertionError, match="gained effective authority"):
        build_public_projection(
            effective,
            core_commit="a" * 40,
            world_commit="b" * 40,
            core_wheel=coordinate,
            action_adapter_wheel=coordinate,
            world_wheel=coordinate,
            core_distribution_version="0.5.0",
            action_adapter_distribution_version="0.1.0",
            world_distribution_version="0.9.0",
        )
