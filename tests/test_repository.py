from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = (ROOT / "opencode-session-toolkit", ROOT / "opencode-session-toolkit-cn")


class RepositoryTest(unittest.TestCase):
    def test_generated_cli_copies_match_canonical_source(self) -> None:
        source = (ROOT / "src" / "opencode_sessions.py").read_bytes()
        expected = hashlib.sha256(source).hexdigest()
        for skill in SKILLS:
            actual = hashlib.sha256(
                (skill / "scripts" / "opencode_sessions.py").read_bytes()
            ).hexdigest()
            self.assertEqual(actual, expected, skill)
            self.assertEqual(
                (skill / "VERSION").read_text(encoding="utf-8"),
                (ROOT / "VERSION").read_text(encoding="utf-8"),
            )

    def test_skill_entrypoints_are_concise_and_reference_real_files(self) -> None:
        for skill in SKILLS:
            skill_md = skill / "SKILL.md"
            text = skill_md.read_text(encoding="utf-8")
            self.assertLessEqual(len(text.splitlines()), 120, skill_md)
            self.assertRegex(
                text, r"\A---\nname: opencode-session-toolkit\ndescription: .+\n---"
            )
            for relative in re.findall(r"`(references/[^`]+\.md)`", text):
                self.assertTrue(
                    (skill / relative).is_file(), f"missing {skill / relative}"
                )

    def test_runtime_packages_do_not_contain_maintainer_install_docs(self) -> None:
        for skill in SKILLS:
            for markdown in skill.rglob("*.md"):
                text = markdown.read_text(encoding="utf-8").lower()
                self.assertNotIn("github release", text, markdown)
                self.assertNotIn("skills@latest add", text, markdown)


if __name__ == "__main__":
    unittest.main()
