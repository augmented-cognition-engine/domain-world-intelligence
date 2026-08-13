from __future__ import annotations

from pathlib import Path

import pytest

from scripts.launch_atrium_ai_command_center import _canvas_directory, _vite_command


def test_showcase_resolves_only_a_core_checkout_with_atrium(tmp_path: Path) -> None:
    canvas = tmp_path / "core/ui/canvas"
    canvas.mkdir(parents=True)
    (canvas / "vite.config.ts").write_text("export default {}\n", encoding="utf-8")
    (canvas / "package.json").write_text("{}\n", encoding="utf-8")

    assert _canvas_directory(tmp_path) == canvas

    with pytest.raises(ValueError, match="not an ACE Core checkout"):
        _canvas_directory(tmp_path / "missing")


def test_showcase_builds_a_loopback_only_vite_command() -> None:
    assert _vite_command(port=5174, open_browser=True) == [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        "5174",
        "--open",
        "/atrium",
    ]
    assert _vite_command(port=5174, open_browser=False)[4:7] == ["--host", "127.0.0.1", "--port"]

    with pytest.raises(ValueError, match="port must be"):
        _vite_command(port=0, open_browser=False)
