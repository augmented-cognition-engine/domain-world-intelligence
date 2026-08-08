#!/usr/bin/env python3
"""Hermetic World Intelligence P2A pack-compiler acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from ace.intelligence import PackCompilationError, compile_pack_document

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pack_root() -> Path:
    try:
        installed = Path(str(files("domain_packs.world_intelligence")))
    except (ModuleNotFoundError, TypeError):
        installed = Path()
    if (installed / "manifest.json").is_file():
        return installed
    return REPO_ROOT / "domain_packs" / "world_intelligence"


PACK_ROOT = _pack_root()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _encoded(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def _pack_material() -> tuple[dict[str, Any], dict[str, bytes]]:
    manifest = _load(PACK_ROOT / "manifest.json")
    resources = {
        item["path"]: (PACK_ROOT / item["path"]).read_bytes()
        for item in manifest["resources"]
    }
    return manifest, resources


def _replace_resource(
    manifest: dict[str, Any],
    resources: dict[str, bytes],
    path: str,
    payload: dict[str, Any],
) -> None:
    encoded = _encoded(payload)
    resources[path] = encoded
    declaration = next(item for item in manifest["resources"] if item["path"] == path)
    declaration["digest"] = f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def compile_world_pack():
    manifest, resources = _pack_material()
    return compile_pack_document(_encoded(manifest), resources)


def run_positive() -> dict[str, Any]:
    compiled = compile_world_pack()
    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    detection = _load(PACK_ROOT / "modules" / "detection.json")
    personas = _load(PACK_ROOT / "modules" / "personas.json")
    synthesis = _load(PACK_ROOT / "modules" / "synthesis.json")
    epistemic = _load(PACK_ROOT / "conformance" / "epistemic_policy.json")

    return {
        "contract": "ace.world-intelligence.p2a-compile-evidence/v1alpha1",
        "pack_id": compiled.metadata.pack_id,
        "pack_version": compiled.metadata.version,
        "compiled_pack_id": compiled.compiled_pack_id,
        "pack_digest": compiled.pack_digest,
        "module_count": len(compiled.modules),
        "entity_type_count": len(ontology["entity_types"]),
        "relation_type_count": len(ontology["relation_types"]),
        "epistemic_status_count": len(epistemic["statuses"]),
        "numeric_detector_ids": sorted(
            item["detector_id"] for item in detection["numeric_delta_rules"]
        ),
        "deferred_generic_detector_strategies": ["categorical", "semantic", "structural"],
        "persona_ids": sorted(item["persona_id"] for item in personas["personas"]),
        "brief_template_ids": sorted(
            item["template_id"] for item in synthesis["brief_templates"]
        ),
        "executable_pack_resources": 0,
        "hidden_truth_score": epistemic["rules"][
            "publisher_has_hidden_universal_truth_score"
        ],
        "political_targeting": False,
        "pack_schema_changed": False,
    }


def _rejected_code(manifest: dict[str, Any], resources: dict[str, bytes]) -> str:
    try:
        compile_pack_document(_encoded(manifest), resources)
    except PackCompilationError as exc:
        return exc.report.diagnostics[0].code
    raise AssertionError("invalid World pack mutation compiled successfully")


def run_negative_cases() -> dict[str, str]:
    results: dict[str, str] = {}

    manifest, resources = _pack_material()
    manifest["execute"] = "python:world.run"
    results["imperative_manifest_control_flow"] = _rejected_code(manifest, resources)

    manifest, resources = _pack_material()
    ontology = _load(PACK_ROOT / "modules" / "ontology.json")
    ontology["relation_types"][0]["target_entity_types"] = ["undeclared_entity"]
    _replace_resource(manifest, resources, "modules/ontology.json", ontology)
    results["unresolved_relation_endpoint"] = _rejected_code(manifest, resources)

    manifest, resources = _pack_material()
    source_mapping = _load(PACK_ROOT / "modules" / "source_mapping.json")
    source_mapping["mappings"][0]["attribute_mappings"].append(
        {"attribute_id": "truth_score", "source_pointer": "/truth", "transform": "copy"}
    )
    _replace_resource(manifest, resources, "modules/source_mapping.json", source_mapping)
    results["unknown_source_attribute"] = _rejected_code(manifest, resources)

    manifest, resources = _pack_material()
    detection = _load(PACK_ROOT / "modules" / "detection.json")
    detection["categorical_rules"] = [
        {"detector_id": "private_event_status", "strategy": "world_private_code"}
    ]
    _replace_resource(manifest, resources, "modules/detection.json", detection)
    results["private_categorical_detector_fork"] = _rejected_code(manifest, resources)

    manifest, resources = _pack_material()
    manifest["resources"].append(
        {
            "resource_id": "world_adapter",
            "path": "adapters/world.py",
            "media_type": "text/x-python",
            "digest": f"sha256:{hashlib.sha256(b'print(1)').hexdigest()}",
        }
    )
    resources["adapters/world.py"] = b"print(1)"
    results["executable_source_adapter_in_pack"] = _rejected_code(manifest, resources)

    return results


def run_acceptance() -> dict[str, Any]:
    positive = run_positive()
    expected = _load(PACK_ROOT / "conformance" / "p2a_expected.json")["expected"]
    if positive != expected:
        raise AssertionError("World P2A positive projection diverged from pinned evidence")
    return {"positive": positive, "negative_cases": run_negative_cases()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--negative", action="store_true", help="include negative-case results")
    args = parser.parse_args()
    result = run_acceptance() if args.negative else run_positive()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
