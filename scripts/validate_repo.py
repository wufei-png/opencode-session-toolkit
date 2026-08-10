#!/usr/bin/env python3
"""Validate source/distribution parity and runtime skill structure."""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "src" / "opencode_sessions.py"
SKILLS = (ROOT / "opencode-session-toolkit", ROOT / "opencode-session-toolkit-cn")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"validation failed: {message}")


def main() -> None:
    ast.parse(CANONICAL.read_text(encoding="utf-8"), filename=str(CANONICAL))
    expected = digest(CANONICAL)
    for skill in SKILLS:
        skill_md = skill / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        if len(text.splitlines()) > 120:
            fail(f"{skill_md} exceeds 120 lines")
        if not re.match(
            r"\A---\nname: opencode-session-toolkit\ndescription: [^\n]+\n---", text
        ):
            fail(f"invalid frontmatter in {skill_md}")
        for relative in re.findall(r"`(references/[^`]+\.md)`", text):
            if not (skill / relative).is_file():
                fail(f"missing referenced file {skill / relative}")
        runtime_cli = skill / "scripts" / "opencode_sessions.py"
        if digest(runtime_cli) != expected:
            fail(f"generated CLI differs: {runtime_cli}")
        if (skill / "VERSION").read_text(encoding="utf-8") != (
            ROOT / "VERSION"
        ).read_text(encoding="utf-8"):
            fail(f"generated VERSION differs: {skill / 'VERSION'}")
        ast.parse(runtime_cli.read_text(encoding="utf-8"), filename=str(runtime_cli))
        if (skill / "scripts" / "export_opencode_sessions.py").exists():
            fail(f"obsolete exporter remains in {skill}")

    result = subprocess.run(
        [sys.executable, str(CANONICAL), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        result.returncode != 0
        or "doctor" not in result.stdout
        or "export" not in result.stdout
    ):
        fail("CLI help smoke test failed")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    version_result = subprocess.run(
        [sys.executable, str(CANONICAL), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if version_result.stdout.strip() != f"opencode-sessions {version}":
        fail("CLI version does not match VERSION")
    print("repository validation: OK")


if __name__ == "__main__":
    main()
