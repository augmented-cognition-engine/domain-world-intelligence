from __future__ import annotations

import importlib.metadata

import pytest


def _has_candidate() -> bool:
    try:
        return importlib.metadata.version("ace-core") == "0.6.0"
    except importlib.metadata.PackageNotFoundError:
        return False


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_candidate(), reason="requires the exact installed ACE 0.7E Core candidate")
async def test_world_v07e_activation_lifecycle_runtime_bindings_and_fail_closed() -> None:
    from scripts.v07e_activation_conformance import CORE_REFERENCE_COORDINATES, run_acceptance

    result = await run_acceptance()

    assert result["pack"]["pack_id"] == "world_intelligence_federal_register_monitor"
    assert result["pack"]["conformance_passed"] is True
    assert result["restart"] == {"initial_exact": True, "rollback_exact": True}
    assert result["historical_reference"]["live_authority"] is False
    assert result["historical_reference"]["rejected_as_runtime_activation"] is True
    assert result["lifecycle"]["upgrade_separately_approved"] == "approval:world-v07e-upgrade"
    assert result["lifecycle"]["rollback_separately_approved"] == "approval:world-v07e-rollback"
    assert result["negative"]["authority_calls"] == 0
    assert result["negative"]["grant_calls"] == 0
    assert result["negative"]["committed_heads"] == 0
    assert set(result["coordinates"].values()).isdisjoint(CORE_REFERENCE_COORDINATES.values())
    assert result["pack"] == {
        "pack_id": "world_intelligence_federal_register_monitor",
        "pack_version": "0.1.0",
        "compiled_pack_id": "pack_ir:3358dd780974acaea5b0ebfc861f826f",
        "pack_digest": "sha256:3358dd780974acaea5b0ebfc861f826f36b334c47bb66200a9bf2e57150ba017",
        "conformance_receipt_id": "pack_conformance:1f0da3850fa13fc5f636f38a32412490",
        "conformance_receipt_digest": ("sha256:1f0da3850fa13fc5f636f38a3241249010adfa87eb0ca946f609d77a37ee61ae"),
        "conformance_passed": True,
    }
    assert result["coordinates"] == {
        "handoff": "activation_onboarding_handoff:39e44660037d554016d034a665c76b57",
        "initial_plan": "intelligence_activation_plan:48e481610646e676933a6459be3221ab",
        "initial_revision": "activation_revision:b066b8923626a8acd3aed163e667bfb6",
        "initial_receipt": "governed_state_commit:fc36194a127a4fa38eae28aa71dba343",
        "upgrade_plan": "intelligence_activation_plan:ee2c82fae487e5ff0bcba86e69f82821",
        "upgrade_revision": "activation_revision:5a448f3ece35a4df5185a5f4f815fb61",
        "rollback_plan": "intelligence_activation_plan:75841bdf53cefd495121f3ce2ce9a590",
        "rollback_revision": "activation_revision:31784ac368453b5d3099e2238d8a5952",
        "rollback_receipt": "governed_state_commit:98c16783fe20e4f1a16509d0a5baa218",
    }
    assert result["bindings"]["monitor_ref"].startswith("monitor:")
    assert result["bindings"]["subscription_ref"].startswith("subscription:")
    assert result["bindings"]["shift_id"].startswith("shift:")
    assert result["bindings"]["brief_id"].startswith("brief:")
