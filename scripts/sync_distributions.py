#!/usr/bin/env python3
"""Copy the canonical CLI into each self-contained skill distribution."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "opencode_sessions.py"
CLI_TARGETS = (
    ROOT / "opencode-session-toolkit" / "scripts" / "opencode_sessions.py",
    ROOT / "opencode-session-toolkit-cn" / "scripts" / "opencode_sessions.py",
)
VERSION_TARGETS = (
    ROOT / "opencode-session-toolkit" / "VERSION",
    ROOT / "opencode-session-toolkit-cn" / "VERSION",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_digest = digest(SOURCE)
    for target in CLI_TARGETS:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE, target)
        target.chmod(0o755)
        if digest(target) != source_digest:
            raise SystemExit(f"Generated copy differs from source: {target}")
        print(f"synced {target.relative_to(ROOT)}")
    for target in VERSION_TARGETS:
        shutil.copyfile(ROOT / "VERSION", target)
        print(f"synced {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
