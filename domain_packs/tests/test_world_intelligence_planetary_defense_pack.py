from __future__ import annotations

import json
from pathlib import Path

from scripts.p2d_live_conflict_correction import compile_planetary_defense_pack

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense"


def test_planetary_defense_pack_is_inert_json_only_and_exactly_pinned() -> None:
    pack = compile_planetary_defense_pack()
    expected = json.loads((PACK_ROOT / "conformance" / "p2d_live_expected.json").read_text(encoding="utf-8"))["pack"]

    assert pack.compiled_pack_id == expected["compiled_pack_id"]
    assert pack.pack_digest == expected["pack_digest"]
    assert len(pack.modules) == expected["module_count"]
    assert all(path.suffix == ".json" for path in PACK_ROOT.rglob("*") if path.is_file())
    assert not tuple(PACK_ROOT.rglob("*.py"))


def test_planetary_defense_pack_declares_conflict_revision_status_and_no_action() -> None:
    pack = compile_planetary_defense_pack()
    contracts = {module.contract for module in pack.modules}
    manifest = json.loads((PACK_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert contracts == {
        "ace.intelligence.detection/v1alpha2",
        "ace.intelligence.epistemic-status/v1alpha2",
        "ace.intelligence.ontology/v1alpha1",
        "ace.intelligence.personas/v1alpha1",
        "ace.intelligence.source-mapping/v1alpha1",
        "ace.intelligence.synthesis/v1alpha2",
    }
    assert {item["authority"] for item in manifest["authority_requests"]} == {"source_read"}
    assert "action" not in json.dumps(manifest).lower()
    assert "delivery" not in json.dumps(manifest).lower()
