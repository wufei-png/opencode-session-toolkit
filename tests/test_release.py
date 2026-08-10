from __future__ import annotations

import hashlib
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_release.py"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class ReleaseTest(unittest.TestCase):
    def test_release_archives_are_reproducible_and_self_contained(self) -> None:
        with (
            tempfile.TemporaryDirectory(prefix="opencode-release-a-") as first_raw,
            tempfile.TemporaryDirectory(prefix="opencode-release-b-") as second_raw,
        ):
            first = Path(first_raw)
            second = Path(second_raw)
            for output in (first, second):
                subprocess.run(
                    [
                        sys.executable,
                        str(BUILD),
                        "--version",
                        VERSION,
                        "--output-dir",
                        str(output),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            for locale in ("en", "cn"):
                name = f"opencode-session-toolkit-{locale}-v{VERSION}.tar.gz"
                self.assertEqual(
                    (first / name).read_bytes(), (second / name).read_bytes()
                )
                with tarfile.open(first / name, "r:gz") as archive:
                    members = {member.name: member for member in archive.getmembers()}
                expected = {
                    "opencode-session-toolkit/SKILL.md",
                    "opencode-session-toolkit/VERSION",
                    "opencode-session-toolkit/agents/openai.yaml",
                    "opencode-session-toolkit/references/cli.md",
                    "opencode-session-toolkit/references/queries.md",
                    "opencode-session-toolkit/references/schema.md",
                    "opencode-session-toolkit/scripts/opencode_sessions.py",
                }
                self.assertEqual(set(members), expected)
                self.assertEqual(
                    members[
                        "opencode-session-toolkit/scripts/opencode_sessions.py"
                    ].mode,
                    0o755,
                )

            checksums = {}
            for line in (first / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest, name = line.split("  ", 1)
                checksums[name] = digest
            for name, expected_digest in checksums.items():
                actual = hashlib.sha256((first / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected_digest)


if __name__ == "__main__":
    unittest.main()
