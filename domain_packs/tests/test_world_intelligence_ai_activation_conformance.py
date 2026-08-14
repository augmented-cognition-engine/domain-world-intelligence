from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ace.testing.domain_pack import run_domain_pack_conformance

PACK_ROOT = Path(__file__).resolve().parents[1] / "world_intelligence_ai"


def _document(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def test_world_ai_pack_passes_the_fixed_activation_fixture_from_recorded_material() -> None:
    manifest_path = PACK_ROOT / "manifest.json"
    fixture_path = PACK_ROOT / "conformance" / "activation_golden_fixture.json"
    manifest = _document(manifest_path)
    fixture = _document(fixture_path)
    live_input = _document(PACK_ROOT / "conformance" / "ai_command_center_live_input.json")

    (case,) = fixture["observations"]
    baseline = json.loads(case["baseline_attributes_json"])
    current = json.loads(case["current_attributes_json"])
    baseline_source, current_source = live_input["sources"][:2]
    baseline_record = json.loads(baseline_source["response_body"])

    assert baseline["document_number"] == baseline_record["document_number"]
    assert baseline["document_title"] == baseline_record["title"]
    assert baseline["source_uri"] == baseline_record["html_url"]
    assert current["source_uri"] == current_source["requested_uri"]
    assert "GOLD EAGLE" in current_source["response_body"]
    assert current["initiative_name"] == "GOLD EAGLE"

    baseline_state_time = _time(case["baseline_as_of"])
    current_state_time = _time(case["current_as_of"])
    baseline_observed_at = _time(baseline_source["observed_at"])
    current_observed_at = _time(current_source["observed_at"])
    baseline_available_at = _time(baseline_source["rechecked_at"])
    current_available_at = _time(current_source["rechecked_at"])

    assert baseline_state_time == _time(f"{baseline['publication_date']}T00:00:00Z")
    assert current_state_time == _time(f"{current['publication_date']}T00:00:00Z")
    assert baseline_state_time < current_state_time
    assert baseline_observed_at < current_observed_at
    assert baseline_available_at < current_available_at
    assert baseline_state_time < baseline_observed_at < baseline_available_at
    assert current_state_time < current_observed_at < current_available_at

    resources = {item["path"]: (PACK_ROOT / item["path"]).read_bytes() for item in manifest["resources"]}
    receipt = run_domain_pack_conformance(
        manifest_document=manifest_path.read_bytes(),
        resources=resources,
        fixture_document=fixture_path.read_bytes(),
    )

    assert receipt.pack_id == "world_intelligence_ai"
    assert receipt.pack_version == "0.2.0"
    assert receipt.compiled_pack_id == "pack_ir:d0d24ae2ef49dedc5278110f5e745932"
    assert receipt.fixture_id == "world_ai_command_center_activation"
    assert receipt.expected_digest == receipt.actual_digest
    assert receipt.passed is True
    assert receipt.diagnostics == ()
