from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ace.intelligence.packs import compile_pack_document

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "domain_packs" / "world_intelligence_ai"


def _compile():
    manifest_bytes = (PACK / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    return compile_pack_document(
        manifest_bytes,
        {resource["path"]: (PACK / resource["path"]).read_bytes() for resource in manifest["resources"]},
    )


def test_ai_topic_pack_compiles_as_inert_domain_configuration() -> None:
    compiled = _compile()
    assert compiled.metadata.pack_id == "world_intelligence_ai"
    assert compiled.metadata.version == "0.2.0"
    assert {module.module_id for module in compiled.modules} == {
        "world_ai_detection",
        "world_ai_ontology",
        "world_ai_personas",
        "world_ai_source_mapping",
        "world_ai_synthesis",
    }


def test_ai_topic_pack_is_json_only_and_source_specific() -> None:
    assert {path.suffix for path in PACK.rglob("*") if path.is_file()} == {".json"}
    mapping = json.loads((PACK / "modules/source_mapping.json").read_text())
    sources = mapping["mappings"]
    assert [source["source_type_ref"] for source in sources[:2]] == [
        "federal_register_ai_policy_document",
        "white_house_ai_policy_release",
    ]
    assert [source["source_type_ref"] for source in sources[2:]] == [
        "reviewed_ai_publication",
    ] * 5
    assert {source["entity_type_id"] for source in sources} == {
        "ai_policy_record",
        "ai_development_record",
    }
    assert {source["source_definition_ref"] for source in sources} == {
        "source_definition:ai-policy-eo-14409",
        "source_definition:white-house-gold-eagle-2026-07-14",
        "source_definition:openai-gpt-5-6-release",
        "source_definition:anthropic-claude-sonnet-5-release",
        "source_definition:deepmind-gemini-3-6-model-cards",
        "source_definition:nist-ai-agent-security-report",
        "source_definition:nvidia-naver-ai-factory-investment",
    }

    manifest = json.loads((PACK / "manifest.json").read_text())
    assert {item["authority"] for item in manifest["authority_requests"]} == {"source_read"}
    assert "entry_points" not in manifest


def test_frozen_world_and_p2c_pack_material_is_unchanged() -> None:
    frozen = {
        "domain_packs/world_intelligence/manifest.json": (
            "3969f9215e0132f90628160b94b7a6638b243452a96a3cc9d15e910163253a97"
        ),
        "domain_packs/world_intelligence_federal_register/manifest.json": (
            "8736e80bdf089921dbfba711dc662c66e4b13ccbf7fc494b15f64796efa03abd"
        ),
    }
    for relative, digest in frozen.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
