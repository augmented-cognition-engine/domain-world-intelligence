from __future__ import annotations

from pathlib import Path

import pytest
import ace.application as ace_application

if not hasattr(ace_application, "IntelligenceResourcePlaneService"):
    pytest.skip(
        "the exact ACE Core 0.8 candidate resource plane is required",
        allow_module_level=True,
    )

from scripts.v08_intelligence_os_acceptance import REQUIRED_LOOP_KINDS, run_acceptance


@pytest.mark.asyncio
async def test_world_journey_is_visible_through_the_unchanged_intelligence_resource_plane(
    tmp_path: Path,
) -> None:
    result = await run_acceptance(tmp_path, core_candidate_commit="test-candidate")

    assert result["core_candidate_commit"] == "test-candidate"
    assert result["domain"] == "world_intelligence"
    assert result["query"]["authority"] == "observe_read"
    assert result["query"]["exact_restart_reopen"] is True
    assert result["loop"]["required_kinds"] == sorted(kind.value for kind in REQUIRED_LOOP_KINDS)
    assert result["loop"]["all_present"] is True
    assert result["loop"]["proposal_applied"] is False
    assert result["loop"]["autonomous_publication"] is False
