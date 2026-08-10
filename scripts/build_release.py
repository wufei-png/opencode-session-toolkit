#!/usr/bin/env python3
"""Build deterministic, self-contained English and Chinese skill archives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import re
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CLI = ROOT / "src" / "opencode_sessions.py"
DISTRIBUTIONS = {
    "en": ROOT / "opencode-session-toolkit",
    "cn": ROOT / "opencode-session-toolkit-cn",
}
IGNORED_NAMES = {".DS_Store", "__pycache__"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(version: str) -> None:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit(f"Version must be semver without a v prefix: {version}")
    repository_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != repository_version:
        raise SystemExit(
            f"Requested version {version} does not match VERSION {repository_version}"
        )
    expected_cli = sha256(SOURCE_CLI)
    for distribution in DISTRIBUTIONS.values():
        runtime_cli = distribution / "scripts" / "opencode_sessions.py"
        if sha256(runtime_cli) != expected_cli:
            raise SystemExit(f"Run scripts/sync_distributions.py: stale {runtime_cli}")
        runtime_version = (distribution / "VERSION").read_text(encoding="utf-8").strip()
        if runtime_version != version:
            raise SystemExit(
                f"Run scripts/sync_distributions.py: stale {distribution / 'VERSION'}"
            )


def iter_files(source: Path) -> list[Path]:
    return sorted(
        path
        for path in source.rglob("*")
        if path.is_file() and not any(part in IGNORED_NAMES for part in path.parts)
    )


def build_archive(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with (
        target.open("wb") as raw_handle,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_handle, mtime=0
        ) as gzip_handle,
        tarfile.open(fileobj=gzip_handle, mode="w") as archive,
    ):
        for path in iter_files(source):
            relative = path.relative_to(source)
            arcname = Path("opencode-session-toolkit") / relative
            data = path.read_bytes()
            info = tarfile.TarInfo(arcname.as_posix())
            info.size = len(data)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o755 if relative.parts[:1] == ("scripts",) else 0o644
            archive.addfile(info, io.BytesIO(data))


def main() -> None:
    args = parse_args()
    validate(args.version)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archives: list[Path] = []
    for locale, source in DISTRIBUTIONS.items():
        target = (
            output_dir / f"opencode-session-toolkit-{locale}-v{args.version}.tar.gz"
        )
        build_archive(source, target)
        archives.append(target)
        print(f"built {target}")
    checksum_lines = [f"{sha256(path)}  {path.name}" for path in archives]
    checksum_path = output_dir / "SHA256SUMS"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"built {checksum_path}")


if __name__ == "__main__":
    main()
