from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ace.intelligence

from scripts.p2a_compile_acceptance import run_acceptance, run_negative_cases, run_positive

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_world_pack_compiles_to_pinned_public_identity():
    assert run_positive() == _load(PACK_ROOT / "conformance" / "p2a_expected.json")["expected"]


def test_world_pack_negative_inventory_fails_closed():
    expected = {
        item["case_id"]: item["expected"]
        for item in _load(PACK_ROOT / "conformance" / "p2a_negative_cases.json")["cases"]
    }
    assert run_negative_cases() == expected


def test_epistemic_policy_is_explicit_and_persona_invariant():
    policy = _load(PACK_ROOT / "conformance" / "epistemic_policy.json")
    assert [item["status_id"] for item in policy["statuses"]] == [
        "observed",
        "attributed_claim",
        "corroborated",
        "disputed",
        "inferred",
        "unknown",
        "scenario",
    ]
    assert policy["rules"] == {
        "source_repetition_is_independent_corroboration": False,
        "publisher_has_hidden_universal_truth_score": False,
        "persona_may_change_evidence_status": False,
        "correction_rewrites_historical_record": False,
        "inference_requires_explicit_label": True,
        "scenario_requires_assumptions_and_watchpoints": True,
    }


def test_pack_is_json_only_and_contains_no_imperative_control_flow():
    manifest = _load(PACK_ROOT / "manifest.json")
    assert all(item["media_type"] == "application/json" for item in manifest["resources"])
    assert not list(PACK_ROOT.rglob("*.py"))

    forbidden_keys = {"execute", "callable", "command", "code", "import", "network"}

    def keys(value):
        if isinstance(value, dict):
            yield from value
            for child in value.values():
                yield from keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from keys(child)

    for path in PACK_ROOT.rglob("*.json"):
        assert forbidden_keys.isdisjoint(keys(_load(path))), path


def test_world_vocabulary_does_not_leak_into_core_or_intelligence():
    intelligence_root = Path(ace.intelligence.__file__).resolve().parent
    forbidden_platform_tokens = {
        "actor_made_claim",
        "actor_supports_policy",
        "political_targeting",
        "provenance_family",
        "reality_change_brief",
        "record_corrects_record",
        "world_intelligence",
    }
    platform_source = "\n".join(
        path.read_text(encoding="utf-8") for path in intelligence_root.rglob("*.py")
    )
    assert all(token not in platform_source for token in forbidden_platform_tokens)


def test_complete_p2a_acceptance_is_reproducible():
    result = run_acceptance()
    assert result["positive"]["pack_schema_changed"] is False
    assert len(result["negative_cases"]) == 5


def test_p2a_manifest_pins_every_acceptance_artifact():
    manifest = _load(PACK_ROOT / "conformance" / "p2a_manifest.json")
    for artifact in manifest["artifacts"]:
        if artifact["path"].startswith("scripts/"):
            path = REPO_ROOT / artifact["path"]
        else:
            path = PACK_ROOT / "conformance" / artifact["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]
