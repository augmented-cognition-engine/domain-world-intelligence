from __future__ import annotations

import subprocess
import sys
import tomllib
import zipfile
from importlib.metadata import distribution
from pathlib import Path

from packaging.requirements import Requirement

ADAPTER_ROOT = Path(__file__).parents[1]
REPOSITORY_ROOT = ADAPTER_ROOT.parents[1]


def _project(path: Path):
    with path.open("rb") as handle:
        return tomllib.load(handle)


def test_builder_executor_is_separate_from_the_inert_root_pack() -> None:
    adapter = _project(ADAPTER_ROOT / "pyproject.toml")["project"]
    root = _project(REPOSITORY_ROOT / "pyproject.toml")["project"]

    assert adapter["name"] == "ace-app-world-ai-builder"
    assert adapter["version"] == "0.1.0"
    assert adapter["entry-points"] == {
        "ace.intelligence_builders": {
            "world_ai_command_center": "ace_world_ai_builder:WorldAIBuilderExecutor",
        }
    }
    assert {Requirement(item).name for item in adapter["dependencies"]} == {
        "ace-core",
        "ace-domain-world-intelligence",
    }
    assert root["name"] == "ace-domain-world-intelligence"
    assert "entry-points" not in root
    assert "ace-app-world-ai-builder" not in root["dependencies"]
    assert (ADAPTER_ROOT / "src/ace_world_ai_builder/executor.py").is_file()
    assert "core.engine" not in "".join(
        path.read_text(encoding="utf-8")
        for path in (ADAPTER_ROOT / "src/ace_world_ai_builder").glob("*.py")
    )
    for pack in (
        "world_intelligence",
        "world_intelligence_ai",
        "world_intelligence_federal_register",
        "world_intelligence_federal_register_monitor",
        "world_intelligence_planetary_defense",
    ):
        assert not any((REPOSITORY_ROOT / "domain_packs" / pack).rglob("*.py"))


def test_builder_executor_wheel_contains_only_the_trusted_adapter_package(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for name in ("README.md", "pyproject.toml"):
        (source / name).write_bytes((ADAPTER_ROOT / name).read_bytes())
    package = source / "src/ace_world_ai_builder"
    package.mkdir(parents=True)
    for path in (ADAPTER_ROOT / "src/ace_world_ai_builder").glob("*.py"):
        (package / path.name).write_bytes(path.read_bytes())
    output = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(output), str(source)],
        check=True,
        capture_output=True,
        text=True,
    )
    (wheel,) = output.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    assert "ace_world_ai_builder/__init__.py" in names
    assert "ace_world_ai_builder/executor.py" in names
    assert "ace_world_ai_builder/journey.py" in names
    assert not any(name.startswith("domain_packs/") for name in names)
    assert not any(name.startswith("scripts/") for name in names)
    entry_points_file = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
    with zipfile.ZipFile(wheel) as archive:
        entry_points_text = archive.read(entry_points_file).decode("utf-8")
    assert entry_points_text == (
        "[ace.intelligence_builders]\n"
        "world_ai_command_center = ace_world_ai_builder:WorldAIBuilderExecutor\n"
    )


def test_installed_entry_point_loads_exact_world_profile() -> None:
    dist = distribution("ace-app-world-ai-builder")
    points = [entry for entry in dist.entry_points if entry.group == "ace.intelligence_builders"]

    assert [(entry.name, entry.value) for entry in points] == [
        ("world_ai_command_center", "ace_world_ai_builder:WorldAIBuilderExecutor")
    ]
    executor = points[0].load()()
    assert executor.profile_id == "intelligence_onboarding_profile:world-ai-command-center"
