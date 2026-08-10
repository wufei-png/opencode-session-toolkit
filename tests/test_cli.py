from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "opencode_sessions.py"


def unix_ms(value: str) -> int:
    return int(
        datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000
    )


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="opencode-toolkit-test-")
        self.root = Path(self.temp_dir.name)
        self.db_path = self.root / "fixture ? #.db"
        self.create_fixture()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def create_fixture(self) -> None:
        connection = sqlite3.connect(self.db_path)
        connection.executescript(
            """
            CREATE TABLE project (
                id TEXT PRIMARY KEY,
                worktree TEXT NOT NULL,
                name TEXT
            );
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                directory TEXT NOT NULL,
                title TEXT NOT NULL,
                version TEXT,
                summary_additions INTEGER,
                summary_deletions INTEGER,
                summary_files INTEGER,
                time_created INTEGER NOT NULL,
                time_updated INTEGER NOT NULL,
                time_archived INTEGER
            );
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                time_created INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            CREATE TABLE part (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                time_created INTEGER NOT NULL,
                data TEXT NOT NULL
            );
            CREATE INDEX message_session_idx ON message(session_id, time_created, id);
            CREATE INDEX part_session_idx ON part(session_id);
            """
        )
        connection.execute(
            "INSERT INTO project VALUES (?, ?, ?)", ("project-1", "/tmp/demo", "Demo")
        )
        connection.executemany(
            "INSERT INTO session VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "ses_percent",
                    "project-1",
                    "/tmp/demo",
                    "100% literal",
                    "1.0",
                    1,
                    2,
                    3,
                    unix_ms("2026-08-09T10:00:00"),
                    unix_ms("2026-08-09T11:00:00"),
                    None,
                ),
                (
                    "ses_other",
                    "project-1",
                    "/tmp/demo",
                    "ordinary title",
                    "1.0",
                    0,
                    0,
                    0,
                    unix_ms("2026-08-10T10:00:00"),
                    unix_ms("2026-08-10T11:00:00"),
                    None,
                ),
            ],
        )
        shared_time = unix_ms("2026-08-09T10:01:00")
        connection.executemany(
            "INSERT INTO message VALUES (?, ?, ?, ?)",
            [
                ("msg_a", "ses_percent", shared_time, json.dumps({"role": "user"})),
                (
                    "msg_b",
                    "ses_percent",
                    shared_time,
                    json.dumps({"role": "assistant", "modelID": "test-model"}),
                ),
            ],
        )
        connection.executemany(
            "INSERT INTO part VALUES (?, ?, ?, ?, ?)",
            [
                (
                    "prt_a1",
                    "msg_a",
                    "ses_percent",
                    shared_time + 1,
                    json.dumps({"type": "text", "text": "hello ``` world"}),
                ),
                (
                    "prt_b1",
                    "msg_b",
                    "ses_percent",
                    shared_time + 2,
                    json.dumps(
                        {
                            "type": "tool",
                            "tool": "shell",
                            "state": {"status": "completed", "title": "check"},
                            "input": {"token": "SECRET_TOOL_INPUT"},
                        }
                    ),
                ),
                (
                    "prt_a2",
                    "msg_a",
                    "ses_percent",
                    shared_time + 3,
                    json.dumps({"type": "reasoning", "text": "SECRET_REASONING"}),
                ),
                (
                    "prt_b2",
                    "msg_b",
                    "ses_percent",
                    shared_time + 4,
                    json.dumps({"type": "text", "text": "done"}),
                ),
            ],
        )
        connection.commit()
        connection.close()

    def run_cli(
        self, *arguments: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(CLI), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(
                f"CLI failed ({result.returncode}): {result.stderr}\n{result.stdout}"
            )
        return result

    def test_literal_substring_does_not_treat_percent_as_wildcard(self) -> None:
        result = self.run_cli(
            "list",
            "--db-path",
            str(self.db_path),
            "--title",
            "%",
            "--format",
            "json",
        )
        rows = json.loads(result.stdout)
        self.assertEqual([row["id"] for row in rows], ["ses_percent"])

    def test_same_timestamp_messages_are_not_duplicated(self) -> None:
        result = self.run_cli(
            "show",
            "--db-path",
            str(self.db_path),
            "ses_percent",
            "--format",
            "json",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(
            [message["id"] for message in payload["messages"]], ["msg_a", "msg_b"]
        )
        self.assertEqual(
            [len(message["parts"]) for message in payload["messages"]], [1, 2]
        )

    def test_safe_show_omits_reasoning_and_complete_tool_payload(self) -> None:
        safe = self.run_cli("show", "--db-path", str(self.db_path), "ses_percent")
        self.assertNotIn("SECRET_REASONING", safe.stdout)
        self.assertNotIn("SECRET_TOOL_INPUT", safe.stdout)
        self.assertIn("Sensitive or non-display parts omitted", safe.stdout)
        self.assertIn("````text", safe.stdout)

        sensitive = self.run_cli(
            "show",
            "--db-path",
            str(self.db_path),
            "ses_percent",
            "--include-sensitive",
        )
        self.assertIn("SECRET_REASONING", sensitive.stdout)
        self.assertIn("SECRET_TOOL_INPUT", sensitive.stdout)
        self.assertIn("sensitive payload export enabled", sensitive.stderr)

    def test_end_date_includes_the_whole_local_calendar_day(self) -> None:
        result = self.run_cli(
            "list",
            "--db-path",
            str(self.db_path),
            "--end",
            "2026-08-09",
            "--format",
            "json",
        )
        rows = json.loads(result.stdout)
        self.assertEqual([row["id"] for row in rows], ["ses_percent"])

    def test_export_is_idempotent_and_refuses_changed_output(self) -> None:
        output_dir = self.root / "export"
        first = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
        )
        self.assertIn("Written files: 1", first.stdout)
        exported = next(output_dir.glob("*.md"))

        second = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
        )
        self.assertIn("Unchanged files: 1", second.stdout)

        exported.write_text("changed", encoding="utf-8")
        third = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
            check=False,
        )
        self.assertEqual(third.returncode, 2)
        self.assertIn("Refusing to overwrite", third.stderr)
        self.assertEqual(exported.read_text(encoding="utf-8"), "changed")

    def test_conflict_preflight_prevents_partial_multi_session_export(self) -> None:
        output_dir = self.root / "preflight"
        self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
        )
        existing = next(output_dir.glob("*.md"))
        existing.write_text("changed", encoding="utf-8")
        result = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--all",
            "--output-dir",
            str(output_dir),
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(output_dir.glob("*ses_other.md")), [])

    def test_blank_filter_cannot_acknowledge_full_export(self) -> None:
        result = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--title",
            "   ",
            "--output-dir",
            str(self.root / "blank-filter"),
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("implicit full export", result.stderr)

    def test_export_dry_run_reports_paths_without_creating_output(self) -> None:
        output_dir = self.root / "dry-run"
        result = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
            "--dry-run",
        )
        self.assertIn("Dry run: no files written", result.stdout)
        self.assertIn("new", result.stdout)
        self.assertFalse(output_dir.exists())

    def test_empty_date_interval_is_rejected(self) -> None:
        result = self.run_cli(
            "list",
            "--db-path",
            str(self.db_path),
            "--start",
            "2026-08-10",
            "--end",
            "2026-08-09",
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--start must not be later", result.stderr)

    def test_doctor_reports_capabilities_without_reading_session_content(self) -> None:
        before = hashlib.sha256(self.db_path.read_bytes()).hexdigest()
        result = self.run_cli(
            "doctor",
            "--db-path",
            str(self.db_path),
            "--format",
            "json",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["read_only"])
        self.assertTrue(payload["commands"]["export"])
        self.assertNotIn("100% literal", result.stdout)
        self.assertEqual(hashlib.sha256(self.db_path.read_bytes()).hexdigest(), before)

    def test_list_works_without_optional_project_table(self) -> None:
        connection = sqlite3.connect(self.db_path)
        connection.execute("DROP TABLE project")
        connection.commit()
        connection.close()
        result = self.run_cli(
            "list",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--format",
            "json",
        )
        rows = json.loads(result.stdout)
        self.assertEqual(rows[0]["project"], "demo")

    def test_overwrite_replaces_output_symlink_without_touching_its_target(
        self,
    ) -> None:
        output_dir = self.root / "symlink-output"
        self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
        )
        exported = next(output_dir.glob("*.md"))
        exported.unlink()
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        exported.symlink_to(outside)

        refused = self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
            check=False,
        )
        self.assertEqual(refused.returncode, 2)
        self.assertTrue(exported.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")

        self.run_cli(
            "export",
            "--db-path",
            str(self.db_path),
            "--session-id",
            "ses_percent",
            "--output-dir",
            str(output_dir),
            "--overwrite",
        )
        self.assertFalse(exported.is_symlink())
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")


if __name__ == "__main__":
    unittest.main()
