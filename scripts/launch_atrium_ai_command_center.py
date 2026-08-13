"""Generate the World AI resource page and open it in Core's local Atrium.

This launcher is presentation plumbing only. World builds an immutable resource-page
artifact through the public Core projection; Core's Vite-only replay seam displays that
artifact without creating a second store, admitting evidence, or granting authority.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPOSITORY_ROOT / "artifacts/atrium-demo/world-ai-resource-page.json"


def _canvas_directory(core_checkout: Path) -> Path:
    checkout = core_checkout.expanduser().resolve()
    canvas = checkout / "core/ui/canvas"
    if not (canvas / "vite.config.ts").is_file() or not (canvas / "package.json").is_file():
        raise ValueError(f"{checkout} is not an ACE Core checkout with the Atrium canvas")
    return canvas


def _vite_command(*, port: int, open_browser: bool) -> list[str]:
    if not 1 <= port <= 65_535:
        raise ValueError("port must be between 1 and 65535")
    command = ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)]
    if open_browser:
        command.extend(["--open", "/atrium"])
    return command


def _prepare_imports(core_checkout: Path) -> None:
    adapter_source = REPOSITORY_ROOT / "adapters/federal_register_source/src"
    for entry in (REPOSITORY_ROOT, adapter_source, core_checkout.expanduser().resolve()):
        value = str(entry)
        if value not in sys.path:
            sys.path.insert(0, value)


def _write_page(payload: dict[str, object], output: Path) -> Path:
    resolved = output.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core", required=True, type=Path, help="Path to an ACE Core checkout")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--port", type=int, default=5174)
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Generate and validate the resource page without starting Atrium",
    )
    arguments = parser.parse_args(argv)

    canvas = _canvas_directory(arguments.core)
    _prepare_imports(arguments.core)
    from scripts.atrium_ai_command_center_demo import build_atrium_page

    payload = asyncio.run(build_atrium_page())
    output = _write_page(payload, arguments.output)
    summary = {
        "atrium_url": f"http://127.0.0.1:{arguments.port}/atrium",
        "builder_stage": payload["demo"]["builder_stage"],
        "output": str(output),
        "product_id": payload["product_id"],
        "resource_count": len(payload["items"]),
        "state": payload["state"],
    }
    print(json.dumps(summary, sort_keys=True))
    if arguments.verify_only:
        return 0
    if not (canvas / "node_modules").is_dir():
        raise RuntimeError(f"Atrium dependencies are not installed; run npm install in {canvas}")

    environment = dict(os.environ)
    environment["ACE_ATRIUM_RESOURCE_PAGE"] = str(output)
    completed = subprocess.run(
        _vite_command(port=arguments.port, open_browser=not arguments.no_open),
        cwd=canvas,
        env=environment,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
