"""Normalize a locally built Python source distribution reproducibly."""

from __future__ import annotations

import argparse
import copy
import gzip
import os
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


def normalize_sdist(archive: Path, *, epoch: int) -> None:
    """Rewrite one ``.tar.gz`` with stable ordering and archive metadata."""

    if epoch < 0:
        raise ValueError("source epoch must be non-negative")
    if not archive.is_file() or not archive.name.endswith(".tar.gz"):
        raise ValueError(f"expected one existing .tar.gz source archive: {archive}")

    temporary: Path | None = None
    try:
        with tarfile.open(archive, mode="r:gz") as source:
            members = source.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)):
                raise ValueError("source archive contains duplicate member names")
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError(f"source archive contains an unsafe member: {name}")

            with tempfile.NamedTemporaryFile(
                prefix=f".{archive.name}.",
                suffix=".tmp",
                dir=archive.parent,
                delete=False,
            ) as raw:
                temporary = Path(raw.name)
                with (
                    gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=epoch) as compressed,
                    tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as target,
                ):
                    for member in sorted(members, key=lambda item: item.name):
                        normalized = copy.copy(member)
                        normalized.uid = 0
                        normalized.gid = 0
                        normalized.uname = ""
                        normalized.gname = ""
                        normalized.mtime = epoch
                        normalized.pax_headers = {}
                        if member.isfile():
                            payload = source.extractfile(member)
                            if payload is None:
                                raise ValueError(f"source archive member has no payload: {member.name}")
                            target.addfile(normalized, payload)
                        else:
                            target.addfile(normalized)
        assert temporary is not None
        os.replace(temporary, archive)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--epoch", type=int, required=True)
    args = parser.parse_args()
    normalize_sdist(args.archive, epoch=args.epoch)


if __name__ == "__main__":
    main()
