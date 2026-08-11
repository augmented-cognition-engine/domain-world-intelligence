#!/usr/bin/env python3
"""Generate the bounded public World measured-intelligence convergence record."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path
from typing import Any, Sequence

import ace
import ace_reference_workspace_action

from scripts.p2c10_independent_correction_reproduction import (
    run_independent_correction_reproduction,
)

CONTRACT = "ace.world-intelligence.measured-intelligence-release-convergence/v1"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_EXPECTED_FIXTURE_DIGEST = "sha256:981183a2464f74f4421bd0a6470f0342a5abae8cfebc1b5a8da1562df26babb1"
_EXPECTED_ORIGINAL = "observation:faf25d26cc88802368cabf3e17538a7d"
_EXPECTED_CORRECTION = "observation:3a1351d6ac306374b8a5b472c192d2b9"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def artifact_identity(path: Path) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"artifact is not a file: {resolved}")
    return {"filename": resolved.name, "sha256": _sha256(resolved)}


def _validated_commit(value: str, *, label: str) -> str:
    if not _COMMIT_RE.fullmatch(value):
        raise ValueError(f"{label} must be a complete lowercase Git commit")
    return value


def validate_core_runtime_outside_checkouts(
    *,
    module_path: Path,
    forbidden_roots: Sequence[Path],
) -> None:
    resolved_module = module_path.resolve(strict=True)
    for root in forbidden_roots:
        resolved_root = root.resolve(strict=True)
        if resolved_module.is_relative_to(resolved_root):
            raise RuntimeError(
                "release convergence requires the built Core artifact; "
                f"ace imported from forbidden checkout {resolved_root}"
            )


def _stable_source_coordinate(reference: dict[str, Any]) -> dict[str, str]:
    return {
        "record_key": reference["record_key"],
        "material_hash": reference["material_hash"],
        "payload_contract": reference["payload_contract"],
    }


def _stable_artifact_projection(artifact: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_key": artifact["artifact_key"],
        "source_family": artifact["source_family"],
        "source_release_id": artifact["source_release_id"],
        "correction_record_id": artifact["correction_record_id"],
        "correction_relation": artifact["correction_relation"],
        "corrects_source_record_id": artifact["corrects_source_record_id"],
        "displayed_statement": artifact["displayed_statement"],
        "source_coverage_complete": artifact["source_coverage_complete"],
        "correction_link_visible": artifact["correction_link_visible"],
        "prior_record_preserved": artifact["prior_record_preserved"],
        "limitations": artifact["limitations"],
    }


def build_public_projection(
    result: dict[str, Any],
    *,
    core_commit: str,
    world_commit: str,
    core_wheel: dict[str, str],
    action_adapter_wheel: dict[str, str],
    world_wheel: dict[str, str],
    core_distribution_version: str,
    action_adapter_distribution_version: str,
    world_distribution_version: str,
) -> dict[str, Any]:
    source_pair = result["source_pair"]
    evaluation = result["evaluation"]
    proposal = result["proposal"]
    replay = result["replay"]
    scope = result["scope"]
    original = source_pair["original_observation"]
    correction = source_pair["correction_observation"]

    if source_pair["fixture_digest"] != _EXPECTED_FIXTURE_DIGEST:
        raise AssertionError("the frozen BLS fixture drifted")
    if original["record_key"] != _EXPECTED_ORIGINAL or correction["record_key"] != _EXPECTED_CORRECTION:
        raise AssertionError("the exact BLS source identities drifted")
    if evaluation["classification"] != "useful" or evaluation["matched_pair_count"] != 2:
        raise AssertionError("the frozen product criterion no longer produces the accepted useful result")
    if evaluation["mean_effect"] != 1.0:
        raise AssertionError("the frozen matched effect drifted")
    if proposal["action"] != "promote":
        raise AssertionError("the frozen useful-to-proposal mapping drifted")
    if proposal["live_effect"] or proposal["selectable"] or not proposal["requires_human_review"]:
        raise AssertionError("the measured-impact proposal gained effective authority")
    if not replay["historical"] or not replay["no_reauthorization"]:
        raise AssertionError("the exact historical replay contract drifted")
    if scope["network_access"] or scope["proposal_applied"]:
        raise AssertionError("the recorded convergence exceeded its authority boundary")

    treatment_scores = [item["correction_quality_score"] for item in result["observed_results"]["treatment"]]
    control_scores = [item["correction_quality_score"] for item in result["observed_results"]["control"]]
    if treatment_scores != [1.0, 1.0] or control_scores != [0.0, 0.0]:
        raise AssertionError("the frozen treatment/control scores drifted")

    return {
        "contract": CONTRACT,
        "candidate_identity": {
            "core_commit": _validated_commit(core_commit, label="core_commit"),
            "world_commit": _validated_commit(world_commit, label="world_commit"),
            "core_distribution_version": core_distribution_version,
            "action_adapter_distribution_version": action_adapter_distribution_version,
            "world_distribution_version": world_distribution_version,
            "artifacts": {
                "core_wheel": core_wheel,
                "action_adapter_wheel": action_adapter_wheel,
                "world_wheel": world_wheel,
            },
        },
        "runtime": {
            "core_import_mode": "installed_distribution_outside_core_checkout",
            "candidate_contract_available": True,
            "network_access": False,
        },
        "public_source_pair": {
            "fixture_id": source_pair["fixture_id"],
            "fixture_digest": source_pair["fixture_digest"],
            "source_policy": source_pair["source_policy"],
            "original": _stable_source_coordinate(original),
            "correction": _stable_source_coordinate(correction),
        },
        "product_policy": result["review_policy"],
        "matched_comparison": {
            "treatment": _stable_artifact_projection(result["artifacts"]["treatment"]),
            "control": _stable_artifact_projection(result["artifacts"]["control"]),
            "treatment_scores": treatment_scores,
            "control_scores": control_scores,
        },
        "measured_result": {
            "classification": evaluation["classification"],
            "matched_pair_count": evaluation["matched_pair_count"],
            "mean_effect": evaluation["mean_effect"],
            "uncertainty": evaluation.get("uncertainty"),
            "limitations": evaluation["limitations"],
        },
        "governed_feedback": {
            "proposed_action": proposal["action"],
            "live_effect": proposal["live_effect"],
            "selectable": proposal["selectable"],
            "requires_human_review": proposal["requires_human_review"],
            "applied": scope["proposal_applied"],
            "historical_replay": replay["historical"],
            "replay_reauthorized": not replay["no_reauthorization"],
        },
        "claim_boundary": {
            "recorded_replay_not_live_monitoring": True,
            "association_not_causality": True,
            "population_performance_claimed": scope["population_correction_performance_claimed"],
            "human_benefit_claimed": scope["human_benefit_claimed"],
            "si4_passed": False,
            "ace_0_6_complete": False,
        },
    }


async def generate(
    *,
    workspace_root: Path,
    core_commit: str,
    world_commit: str,
    core_wheel_path: Path,
    action_adapter_wheel_path: Path,
    world_wheel_path: Path,
    forbidden_core_roots: Sequence[Path],
) -> dict[str, Any]:
    if ace.__file__ is None or ace_reference_workspace_action.__file__ is None:
        raise RuntimeError("installed candidate distributions do not expose concrete module paths")
    validate_core_runtime_outside_checkouts(
        module_path=Path(ace.__file__),
        forbidden_roots=forbidden_core_roots,
    )
    result = await run_independent_correction_reproduction(workspace_root)
    return build_public_projection(
        result,
        core_commit=core_commit,
        world_commit=world_commit,
        core_wheel=artifact_identity(core_wheel_path),
        action_adapter_wheel=artifact_identity(action_adapter_wheel_path),
        world_wheel=artifact_identity(world_wheel_path),
        core_distribution_version=importlib.metadata.version("ace-core"),
        action_adapter_distribution_version=importlib.metadata.version("ace-reference-workspace-action"),
        world_distribution_version=importlib.metadata.version("ace-domain-world-intelligence"),
    )


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_root", type=Path)
    parser.add_argument("--core-commit", required=True)
    parser.add_argument("--world-commit", required=True)
    parser.add_argument("--core-wheel", required=True, type=Path)
    parser.add_argument("--action-adapter-wheel", required=True, type=Path)
    parser.add_argument("--world-wheel", required=True, type=Path)
    parser.add_argument("--forbid-core-root", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.workspace_root.mkdir(parents=True, exist_ok=True)
    projection = asyncio.run(
        generate(
            workspace_root=args.workspace_root,
            core_commit=args.core_commit,
            world_commit=args.world_commit,
            core_wheel_path=args.core_wheel,
            action_adapter_wheel_path=args.action_adapter_wheel,
            world_wheel_path=args.world_wheel,
            forbidden_core_roots=tuple(args.forbid_core_root),
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(_canonical_json(projection), encoding="utf-8")
    print(f"Wrote {args.output}: {_sha256(args.output)}")


if __name__ == "__main__":
    main()
