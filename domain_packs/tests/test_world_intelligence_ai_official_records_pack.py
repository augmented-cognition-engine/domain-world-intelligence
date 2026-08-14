from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ace.intelligence.packs import compile_pack_document
from ace.testing.domain_pack import run_domain_pack_conformance

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "domain_packs" / "world_intelligence_ai_official_records"
CURRENT_AI_PACK = ROOT / "domain_packs" / "world_intelligence_ai"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pack_material() -> tuple[bytes, dict[str, bytes]]:
    manifest_document = (PACK / "manifest.json").read_bytes()
    manifest = json.loads(manifest_document)
    resources = {item["path"]: (PACK / item["path"]).read_bytes() for item in manifest["resources"]}
    return manifest_document, resources


def test_official_records_pack_is_one_distinct_inert_two_source_program() -> None:
    manifest_document, resources = _pack_material()
    manifest = json.loads(manifest_document)
    compiled = compile_pack_document(manifest_document, resources)

    assert compiled.metadata.pack_id == "world_intelligence_ai_official_records"
    assert compiled.metadata.version == "1.0.0"
    assert compiled.compiled_pack_id == "pack_ir:df6127f517247e7f5eac1175aaa9ca89"
    assert compiled.pack_digest == "sha256:df6127f517247e7f5eac1175aaa9ca89721e1bd6ac95b59d96061df98b99bde5"
    assert compiled.metadata.pack_id != _load(CURRENT_AI_PACK / "manifest.json")["metadata"]["pack_id"]
    assert {item["requirement_id"] for item in manifest["capability_requirements"]} == {
        "ai_policy_federal_register_snapshot",
        "ai_policy_white_house_snapshot",
    }
    assert {item["request_id"] for item in manifest["authority_requests"]} == {
        "read_ai_policy_federal_register_document",
        "read_ai_policy_white_house_release",
    }
    assert {item["authority"] for item in manifest["authority_requests"]} == {"source_read"}
    assert "entry_points" not in manifest
    assert {path.suffix for path in PACK.rglob("*") if path.is_file()} == {".json"}


def test_official_records_pack_preserves_the_exact_policy_progression_program() -> None:
    ontology = _load(PACK / "modules/ontology.json")
    mappings = _load(PACK / "modules/source_mapping.json")["mappings"]
    detection = _load(PACK / "modules/detection.json")
    personas = _load(PACK / "modules/personas.json")
    synthesis = _load(PACK / "modules/synthesis.json")

    assert [item["entity_type_id"] for item in ontology["entity_types"]] == ["ai_policy_record"]
    assert [item["mapping_id"] for item in mappings] == [
        "ai_policy_record_snapshot",
        "ai_policy_implementation_snapshot",
    ]
    assert [item["source_definition_ref"] for item in mappings] == [
        "source_definition:ai-policy-eo-14409",
        "source_definition:white-house-gold-eagle-2026-07-14",
    ]
    (detector,) = detection["categorical_transition_rules"]
    assert detector == {
        "detector_id": "ai_policy_implementation_progression",
        "entity_type_id": "ai_policy_record",
        "attribute_id": "development_stage",
        "baseline": "prior_snapshot",
        "context_attribute_ids": ["executive_order_number", "policy_topic"],
        "transitions": [{"from_value": "directive_issued", "to_value": "implementation_reported"}],
        "shift_type": "official_ai_policy_progression",
        "signal_type": "official_ai_policy_development",
    }
    assert personas["signal_routing_rules"] == [
        {
            "routing_rule_id": "route_official_ai_policy_development",
            "signal_type": "official_ai_policy_development",
            "persona_ids": ["ai_policy_researcher"],
            "minimum_confidence": 0.8,
            "brief_template_id": "ai_policy_reality_brief",
        }
    ]
    (template,) = synthesis["brief_templates"]
    assert template["template_id"] == "ai_policy_reality_brief"
    assert template["required_sections"] == [
        "what_changed",
        "why_it_matters",
        "how_we_know",
        "when_it_changed",
        "unknowns",
        "limitations",
    ]


def test_official_records_fixed_activation_fixture_passes_exactly() -> None:
    manifest_document, resources = _pack_material()
    receipt = run_domain_pack_conformance(
        manifest_document=manifest_document,
        resources=resources,
        fixture_document=(PACK / "conformance/activation_golden_fixture.json").read_bytes(),
    )

    assert receipt.pack_id == "world_intelligence_ai_official_records"
    assert receipt.pack_version == "1.0.0"
    assert receipt.compiled_pack_id == "pack_ir:df6127f517247e7f5eac1175aaa9ca89"
    assert receipt.fixture_id == "world_ai_official_records_activation"
    assert receipt.fixture_digest == "sha256:e415405670e3709c23f9ea3ade34c4a4606c24ffe26ba53ad5f165ecc12521a9"
    assert receipt.expected_digest == receipt.actual_digest
    assert receipt.passed is True
    assert receipt.diagnostics == ()


def test_recorded_inventory_is_exactly_two_official_lineages_and_never_freshness() -> None:
    inventory = _load(PACK / "conformance/recorded_sources.json")
    fixture = _load(PACK / "conformance/activation_golden_fixture.json")
    (case,) = fixture["observations"]
    materials = inventory["materials"]

    assert inventory["source_group_id"] == "official_records"
    assert inventory["subject_binding"] == {
        "subject_binding_id": "published_ai_policy_record",
        "entity_type_id": "ai_policy_record",
        "entity_ref": "entity:ai-policy/executive-order-14409",
    }
    assert [item["material_key"] for item in materials] == [
        "federal_register_eo_14409",
        "white_house_gold_eagle_implementation",
    ]
    assert [item["captured_payload_json"] for item in materials] == [
        case["baseline_attributes_json"],
        case["current_attributes_json"],
    ]
    for material in materials:
        assert material["captured_payload_digest"] == (
            "sha256:" + hashlib.sha256(material["captured_payload_json"].encode("utf-8")).hexdigest()
        )
        assert material["source_published_at"] == material["event_effective_at"]
    limitations = " ".join(inventory["limitations"]).lower()
    assert "recorded" in limitations
    assert "not proof of a current network response" in limitations
    assert "verifies no freshness" in limitations
    assert "independent non-government corroboration" in limitations


def test_official_records_pack_is_an_internal_target_of_the_one_world_profile() -> None:
    broad_profile = _load(CURRENT_AI_PACK / "onboarding_profile.json")
    world_profiles = [
        _load(path)
        for path in (ROOT / "domain_packs").glob("*/onboarding_profile.json")
        if _load(path).get("domain_label") == "World Intelligence"
    ]

    assert not (PACK / "onboarding_profile.json").exists()
    assert [item["profile_id"] for item in world_profiles] == [
        "intelligence_onboarding_profile:world-ai-command-center"
    ]
    (official_records,) = [
        item for item in broad_profile["source_groups"] if item["source_group_id"] == "official_records"
    ]
    assert [
        item["source_group_id"] for item in broad_profile["source_groups"] if item["default_selected"]
    ] == ["official_records"]
    assert {
        "us_federal_register_ai_policy",
        "white_house_ai_policy",
    }.issubset(official_records["source_ids"])
