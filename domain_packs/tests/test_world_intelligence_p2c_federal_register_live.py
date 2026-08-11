from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.p2c_federal_register_live_acceptance import (
    EXPECTED_NAME,
    compile_live_pack,
    load_fixture,
    run_acceptance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_exact_live_admission_replay_and_restart_are_pinned() -> None:
    projection, environment, conformance = await run_acceptance()

    assert projection == load_fixture(EXPECTED_NAME)["expected"]
    assert conformance.first.replayed is False
    assert conformance.exact_replay.replayed is True
    assert conformance.restarted_replay.replayed is True
    assert environment.adapter.capture_calls == environment.transport.calls == 1
    assert len(environment.immutable_store.records) == 5
    assert len(environment.immutable_store.receipts) == 1


@pytest.mark.asyncio
async def test_live_boundary_is_visible_read_only_and_stops_before_intelligence() -> None:
    projection, environment, conformance = await run_acceptance()
    first = conformance.first

    assert first.observation.mode.value == "live"
    assert first.entity_snapshot.mode.value == "live"
    assert first.source_snapshot.acquisition_mode.value == "live"
    assert first.reusable_authority is False
    assert environment.committed_activation.live_authority is False
    assert projection["scope"] == {
        "admission_disposition": "committed",
        "capture_calls": 1,
        "exact_record_order": [
            "source_acquisition",
            "source_snapshot",
            "observation",
            "entity_snapshot",
            "source_admission",
        ],
        "live_acquisition": True,
        "network_access": False,
        "prohibited_record_kinds_present": [],
        "reusable_authority": False,
        "transport_calls": 1,
        "transport_fixture_only": True,
    }
    assert {record.record_kind for record in environment.immutable_store.records.values()} == {
        "source_acquisition",
        "source_snapshot",
        "observation",
        "entity_snapshot",
        "source_admission",
    }


@pytest.mark.asyncio
async def test_official_format_reference_and_legal_status_survive_mapping() -> None:
    projection, _, _ = await run_acceptance()
    attributes = projection["mapped_result"]["attributes"]

    assert attributes["official_pdf_url"] == ("https://www.govinfo.gov/content/pkg/FR-2026-08-07/pdf/2026-16197.pdf")
    assert attributes["legal_status_notice"] == ("FederalRegister.gov is not the official legal edition.")
    assert attributes["verification_reference"] == (
        "The govinfo.gov PDF is the official-format verification reference."
    )


def test_additive_live_pack_compiles_without_mutating_frozen_world_pack() -> None:
    compiled = compile_live_pack()
    assert compiled.compiled_pack_id == "pack_ir:1847032fc5301bba9b6f85d3d091400d"
    assert compiled.pack_digest == ("sha256:1847032fc5301bba9b6f85d3d091400dfc3e2679496e2932d4345bddfb799d1f")

    frozen = {
        "manifest.json": "3969f9215e0132f90628160b94b7a6638b243452a96a3cc9d15e910163253a97",
        "modules/ontology.json": "211218d7543e0d59d4c094cb0e44955c073bac7d0e6d44ac5ec1db81663fb67f",
        "modules/source_mapping.json": "66bcd6c17e467aeaca58a4777fe58115129bd1e0c02d3b2928d1a68b81eb0e1b",
        "conformance/p2b_scenario.json": "cf6163b70253ae0e32fc6e750c842c06dfdde9592b421947bcb8debff9948d04",
    }
    pack_root = REPO_ROOT / "domain_packs" / "world_intelligence"
    for relative, expected in frozen.items():
        assert hashlib.sha256((pack_root / relative).read_bytes()).hexdigest() == expected


def test_additive_pack_and_fixture_are_declarative_and_network_free() -> None:
    pack_root = REPO_ROOT / "domain_packs" / "world_intelligence_federal_register"
    suffixes = {path.suffix for path in pack_root.rglob("*") if path.is_file()}
    assert suffixes == {".json"}
    fixture = json.loads((pack_root / "conformance" / "p2c_live_source_input.json").read_text())
    assert fixture["transport_fixture"]["fixture_only"] is True
    assert fixture["transport_fixture"]["network_access"] is False
