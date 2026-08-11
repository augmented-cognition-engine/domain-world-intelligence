"""Release contract for the ACE World Intelligence 0.10.0 root distribution.

These assertions are the publishable-identity gate. They pin what a consumer of
``ace-domain-world-intelligence`` receives from PyPI: the exact version, the exact
supported interpreter range, the exact ``ace-core`` compatibility window, and the
guarantee that the Federal Register source adapter stays a separate distribution
that the root distribution never pulls in. They also pin that the root
distribution mapping ships inert data only -- JSON Domain Pack resources with no
importable code, no test package, and nothing that executes on install.

``packaging`` is a locked transitive dependency of the synced environment; it is
imported directly rather than guarded, because a release gate must fail loudly
instead of silently skipping.
"""

from __future__ import annotations

import gzip
import io
import tarfile
import tomllib
from pathlib import Path
from typing import Any

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from scripts.normalize_sdist import normalize_sdist

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"
ADAPTER_ROOT = REPO_ROOT / "adapters" / "federal_register_source"
ADAPTER_PYPROJECT = ADAPTER_ROOT / "pyproject.toml"

ROOT_DISTRIBUTION = "ace-domain-world-intelligence"
ADAPTER_DISTRIBUTION = "ace-ext-world-federal-register-source"
ADAPTER_IMPORT_PACKAGE = "ace_world_federal_register_source"

EXPECTED_ROOT_VERSION = "0.10.0"
EXPECTED_REQUIRES_PYTHON = ">=3.12,<3.13"
EXPECTED_ACE_CORE_REQUIREMENT = "ace-core>=0.6.0,<0.7"
EXPECTED_ACE_CORE_SPECIFIER = ">=0.6.0,<0.7"

DOMAIN_PACK_DIRECTORIES = (
    REPO_ROOT / "domain_packs" / "world_intelligence",
    REPO_ROOT / "domain_packs" / "world_intelligence_federal_register",
    REPO_ROOT / "domain_packs" / "world_intelligence_federal_register_monitor",
    REPO_ROOT / "domain_packs" / "world_intelligence_ai",
    REPO_ROOT / "domain_packs" / "world_intelligence_planetary_defense",
)


def _load_pyproject(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


ROOT_PROJECT = _load_pyproject(ROOT_PYPROJECT)
ADAPTER_PROJECT = _load_pyproject(ADAPTER_PYPROJECT)


def _root_runtime_requirements() -> list[Requirement]:
    return [Requirement(entry) for entry in ROOT_PROJECT["project"]["dependencies"]]


def test_root_distribution_is_named_and_versioned_exactly_for_the_release() -> None:
    project = ROOT_PROJECT["project"]

    assert project["name"] == ROOT_DISTRIBUTION
    assert project["version"] == EXPECTED_ROOT_VERSION
    assert Version(project["version"]) == Version(EXPECTED_ROOT_VERSION)
    # A static version is part of the contract: the published version must be
    # readable from pyproject.toml alone, not computed at build time.
    assert "version" not in project.get("dynamic", [])


def test_repository_identity_license_and_public_links_are_complete() -> None:
    project = ROOT_PROJECT["project"]
    expected_urls = {
        "Homepage": "https://github.com/augmented-cognition-engine/domain-world-intelligence",
        "Repository": "https://github.com/augmented-cognition-engine/domain-world-intelligence",
        "Issues": "https://github.com/augmented-cognition-engine/domain-world-intelligence/issues",
        "Changelog": "https://github.com/augmented-cognition-engine/domain-world-intelligence/blob/main/CHANGELOG.md",
        "Roadmap": "https://github.com/augmented-cognition-engine/domain-world-intelligence/blob/main/ROADMAP.md",
    }

    assert project["license"] == "Apache-2.0"
    assert project["urls"] == expected_urls
    for name in (
        "LICENSE",
        "NOTICE",
        "README.md",
        "ROADMAP.md",
        "CHANGELOG.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
    ):
        assert (REPO_ROOT / name).is_file(), name

    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in (
        "independently versioned ACE domain product",
        "JSON-only Domain Pack",
        "## What you install, and what you get",
        "## Product loop",
        "## Connector boundary",
        "## Guardrails",
        "## Roadmap and project status",
        "## Community and security",
    ):
        assert phrase in readme


def test_root_requires_python_is_exactly_the_3_12_series() -> None:
    project = ROOT_PROJECT["project"]

    assert project["requires-python"] == EXPECTED_REQUIRES_PYTHON

    specifier = SpecifierSet(project["requires-python"])
    assert specifier == SpecifierSet(EXPECTED_REQUIRES_PYTHON)
    assert specifier.contains(Version("3.12.0"))
    assert specifier.contains(Version("3.12.11"))
    assert not specifier.contains(Version("3.11.9"))
    assert not specifier.contains(Version("3.13.0"))


def test_root_depends_only_on_the_ace_core_0_6_compatibility_window() -> None:
    dependencies = ROOT_PROJECT["project"]["dependencies"]

    assert dependencies == [EXPECTED_ACE_CORE_REQUIREMENT]

    (requirement,) = _root_runtime_requirements()
    assert canonicalize_name(requirement.name) == "ace-core"
    assert requirement.extras == set()
    assert requirement.marker is None
    assert requirement.url is None
    assert requirement.specifier == SpecifierSet(EXPECTED_ACE_CORE_SPECIFIER)
    assert requirement.specifier.contains(Version("0.6.0"))
    assert requirement.specifier.contains(Version("0.6.9"))
    assert not requirement.specifier.contains(Version("0.5.0"))
    assert not requirement.specifier.contains(Version("0.7.0"))


def test_federal_register_adapter_is_a_separate_distribution() -> None:
    adapter = ADAPTER_PROJECT["project"]

    assert ADAPTER_PYPROJECT.is_file()
    assert adapter["name"] == ADAPTER_DISTRIBUTION
    assert adapter["name"] != ROOT_DISTRIBUTION
    assert adapter["version"] == "0.3.0"
    assert adapter["requires-python"] == EXPECTED_REQUIRES_PYTHON
    assert adapter["license"] == "Apache-2.0"
    assert adapter["readme"] == "README.md"
    assert adapter["dependencies"] == [EXPECTED_ACE_CORE_REQUIREMENT]
    assert adapter["urls"] == {
        "Repository": "https://github.com/augmented-cognition-engine/domain-world-intelligence",
        "Issues": "https://github.com/augmented-cognition-engine/domain-world-intelligence/issues",
    }

    # The adapter carries its own build backend, so it is built and released on
    # its own cadence rather than as part of the root distribution.
    assert ADAPTER_PROJECT["build-system"]["build-backend"] == "setuptools.build_meta"

    # The adapter's importable code lives outside every path the root
    # distribution maps, so no root build can sweep it in.
    adapter_package = ADAPTER_ROOT / "src" / ADAPTER_IMPORT_PACKAGE
    assert adapter_package.is_dir()
    assert (adapter_package / "adapter.py").is_file()
    assert (REPO_ROOT / "domain_packs") not in adapter_package.parents


def test_adapter_is_absent_from_the_root_runtime_dependency_closure() -> None:
    project = ROOT_PROJECT["project"]

    runtime_names = {canonicalize_name(requirement.name) for requirement in _root_runtime_requirements()}
    assert canonicalize_name(ADAPTER_DISTRIBUTION) not in runtime_names

    # No optional extra may reintroduce the adapter for installing consumers.
    for extra_requirements in project.get("optional-dependencies", {}).values():
        extra_names = {canonicalize_name(Requirement(entry).name) for entry in extra_requirements}
        assert canonicalize_name(ADAPTER_DISTRIBUTION) not in extra_names

    # The adapter is referenced only by the local dev group and its uv path
    # source. Dependency groups and tool.uv.sources are not published metadata,
    # so neither reaches a PyPI consumer.
    dev_group = ROOT_PROJECT["dependency-groups"]["dev"]
    assert ADAPTER_DISTRIBUTION in dev_group
    assert ROOT_PROJECT["tool"]["uv"]["sources"][ADAPTER_DISTRIBUTION] == {
        "path": "adapters/federal_register_source",
        "editable": True,
    }


def test_release_workflows_pin_public_core_and_keep_adapter_publication_separate() -> None:
    ci = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    publish = (REPO_ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")

    assert 'ACE_CORE_VERSION: "0.6.0"' in ci
    assert 'ROOT_VERSION: "0.10.0"' in ci
    assert "ACE_CORE_CANDIDATE_SHA" not in ci
    assert "eaa51ea704e9162363a4483d1f7d7779778b953ed2a2d80b67dfb332e1cd3f62" in ci
    assert "ace_reference_workspace_action-0.2.0-py3-none-any.whl" in ci
    assert 'python scripts/normalize_sdist.py "dist/${ROOT_SDIST}"' in ci
    assert 'cmp "dist/${ROOT_WHEEL}" "${reproducible}/${ROOT_WHEEL}"' in ci
    assert 'cmp "dist/${ROOT_SDIST}" "${reproducible}/${ROOT_SDIST}"' in ci

    assert "default: v0.10.0" in publish
    assert "packages-dir: dist" in publish
    assert "release-source-adapter:" in publish
    assert "ace_ext_world_federal_register_source-0.3.0-py3-none-any.whl" in publish
    assert 'gh release upload "${TAG}" dist/source-adapter/*' in publish
    assert 'python scripts/normalize_sdist.py "dist/${EXPECTED_SDIST}"' in publish


def test_source_archive_normalizer_removes_build_time_metadata(tmp_path: Path) -> None:
    def build_unstable_archive(path: Path, *, build_time: int) -> None:
        with (
            path.open("wb") as raw,
            gzip.GzipFile(filename=path.name, mode="wb", fileobj=raw, mtime=build_time) as compressed,
            tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive,
        ):
            for name, payload in (("example/data.json", b"{}\n"), ("example/PKG-INFO", b"Version: 0.10.0\n")):
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                member.mtime = build_time
                member.uid = build_time
                member.gid = build_time
                member.uname = "builder"
                member.gname = "builder"
                archive.addfile(member, io.BytesIO(payload))

    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    build_unstable_archive(first, build_time=1_700_000_001)
    build_unstable_archive(second, build_time=1_700_000_099)
    assert first.read_bytes() != second.read_bytes()

    epoch = 1_700_000_000
    normalize_sdist(first, epoch=epoch)
    normalize_sdist(second, epoch=epoch)
    assert first.read_bytes() == second.read_bytes()
    assert int.from_bytes(first.read_bytes()[4:8], byteorder="little") == epoch

    with tarfile.open(first, mode="r:gz") as archive:
        members = archive.getmembers()
    assert [member.name for member in members] == sorted(member.name for member in members)
    assert {member.mtime for member in members} == {epoch}
    assert {member.uid for member in members} == {0}
    assert {member.gid for member in members} == {0}
    assert {member.uname for member in members} == {""}
    assert {member.gname for member in members} == {""}


def test_root_distribution_mapping_stays_inert_and_data_only() -> None:
    setuptools_config = ROOT_PROJECT["tool"]["setuptools"]

    assert setuptools_config["packages"]["find"] == {
        "where": ["."],
        "include": ["domain_packs*"],
        "exclude": ["domain_packs.tests*"],
        "namespaces": True,
    }
    # Only explicitly declared data patterns ship; nothing is swept in implicitly.
    assert setuptools_config["include-package-data"] is False

    package_data = setuptools_config["package-data"]
    assert set(package_data) == {
        "domain_packs.world_intelligence",
        "domain_packs.world_intelligence_ai",
        "domain_packs.world_intelligence_planetary_defense",
        "domain_packs.world_intelligence_federal_register",
        "domain_packs.world_intelligence_federal_register_monitor",
    }
    for patterns in package_data.values():
        assert patterns == ["*.json", "modules/*.json", "conformance/*.json"]

    # Inert means nothing runs on install or import of the distribution.
    project = ROOT_PROJECT["project"]
    assert "scripts" not in project
    assert "gui-scripts" not in project
    assert "entry-points" not in project

    # Data-only means the mapped package tree holds JSON resources and no code.
    for pack_directory in DOMAIN_PACK_DIRECTORIES:
        assert pack_directory.is_dir()
        shipped = sorted(path for path in pack_directory.rglob("*.json") if path.is_file())
        assert shipped, pack_directory
        every_file = sorted(path for path in pack_directory.rglob("*") if path.is_file())
        assert every_file == shipped

    # The test package is excluded from the mapping and must never be shipped.
    assert (REPO_ROOT / "domain_packs" / "tests").is_dir()
    assert not (REPO_ROOT / "domain_packs" / "__init__.py").exists()
