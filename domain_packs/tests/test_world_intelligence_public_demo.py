from __future__ import annotations

import asyncio
import json

import pytest

from scripts import public_demo


@pytest.fixture(scope="module")
def demo_data():
    return asyncio.run(public_demo.collect_demo_data())


def test_demo_is_bound_to_the_exact_accepted_release_contract(demo_data):
    assert demo_data["scenario"] == {
        "id": "meridia_reservoir_release_72h",
        "mode": "PREPARED",
        "state": "FROZEN",
        "kind": "synthetic, hermetic, redistributable fixture",
        "is_live": False,
        "generated_at": "2026-03-12T14:11:20Z",
        "as_of": "2026-03-12T14:10:00Z",
    }
    public_demo._assert_release_contract(demo_data)
    assert demo_data["identities"] == {
        "case_id": "case:412426eee708d56f6bda931ccf9e5d8b",
        "brief_id": "brief:25d8232c9bfa27050bdcb160fb75f06c",
        "status_projection_id": (
            "brief_derivation_family_status_projection:3500889a2d75af7a5484a681afbee34c"
        ),
        "impact_projection_id": (
            "supersession_impact_projection:f3723de8e9ac5c4390c5c46137f3765e"
        ),
    }


def test_demo_data_exposes_real_claim_status_and_derivation_proofs(demo_data):
    graph = demo_data["evidence_graph"]
    assert graph["corroboration"] == {
        "claim_id": "grounded_claim:d3618122209bab77b540f6336ef7b57e",
        "required_distinct_roots": 2,
        "observed_distinct_roots": 2,
        "publisher_count_is_independence": False,
    }
    assert len(graph["ledger_family"]["derived_records"]) == 2
    assert demo_data["brief"]["claim_count"] == 11
    assert demo_data["brief"]["claims_per_status"] == {
        "ace_inference": 3,
        "admitted_record": 2,
        "attributed_claim": 1,
        "corroborated": 1,
        "disputed": 1,
        "scenario": 1,
        "unknown": 2,
    }


def test_html_is_deterministic_self_contained_and_data_faithful(demo_data):
    first = public_demo.render_html(demo_data)
    second = public_demo.render_html(demo_data)
    assert first == second
    assert "https://" not in first
    assert "http://" not in first
    assert "<script src=" not in first
    assert "@import" not in first
    for value in (
        demo_data["identities"]["case_id"],
        demo_data["identities"]["brief_id"],
        demo_data["identities"]["status_projection_id"],
        demo_data["identities"]["impact_projection_id"],
    ):
        assert value in first
    embedded = first.split('<script type="application/json" id="ace-demo-data">', 1)[1]
    embedded = embedded.split("</script>", 1)[0]
    assert json.loads(embedded) == demo_data


def test_html_states_the_trust_boundary_and_does_not_pose_as_live(demo_data):
    page = public_demo.render_html(demo_data)
    assert "PREPARED · FROZEN" in page
    assert "SYNTHETIC 72-HOUR SCENARIO" in page
    assert "NO LIVE DATA · NO EXTERNAL ACTION" in page
    assert "Impact means dependency, not falsehood." in page
    assert "Byte-identical replay" in page
    assert "3 publishers ≠ 3 sources" in page
    assert "production-ready" not in page.lower()


def test_write_demo_honors_output_dir_and_is_byte_deterministic(tmp_path, demo_data, monkeypatch):
    async def fixed_data():
        return demo_data

    monkeypatch.setattr(public_demo, "collect_demo_data", fixed_data)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_data, first_html, _ = asyncio.run(public_demo.write_demo(first_dir))
    second_data, second_html, _ = asyncio.run(public_demo.write_demo(second_dir))
    assert first_data.read_bytes() == second_data.read_bytes()
    assert first_html.read_bytes() == second_html.read_bytes()
    assert first_data.parent == first_dir
    assert first_html.parent == first_dir


def test_command_accepts_an_explicit_output_directory(tmp_path, demo_data, monkeypatch, capsys):
    async def fixed_data():
        return demo_data

    monkeypatch.setattr(public_demo, "collect_demo_data", fixed_data)
    output = tmp_path / "release-proof"
    assert public_demo.main(["--output-dir", str(output)]) == 0
    assert (output / "demo-data.json").is_file()
    assert (output / "index.html").is_file()
    stdout = capsys.readouterr().out
    assert "PREPARED / FROZEN" in stdout
    assert str(output / "index.html") in stdout
