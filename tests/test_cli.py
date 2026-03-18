import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import _bootstrap
from bookmark_checker.cli import main
from bookmark_checker.models import CheckResult


class CliTests(unittest.TestCase):
    @patch("bookmark_checker.cli.run_checks")
    def test_main_writes_json_output_and_returns_failure_when_problems_exist(self, mock_run_checks):
        mock_run_checks.return_value = [
            CheckResult("A", "https://example.com/a", "ok", "HTTP 200", 200, "https://example.com/a"),
            CheckResult("B", "https://example.com/b", "client_error", "HTTP 404", 404, "https://example.com/b"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            bookmark_file = Path(tmpdir) / "bookmarks.html"
            output_file = Path(tmpdir) / "result.json"
            bookmark_file.write_text('<a href="https://example.com/a">A</a>', encoding="utf-8")

            exit_code = main(
                [
                    "check",
                    str(bookmark_file),
                    "--format",
                    "json",
                    "--output",
                    str(output_file),
                    "--only-problems",
                ]
            )

            payload = json.loads(output_file.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["status"], "client_error")

    @patch("bookmark_checker.cli.run_checks")
    def test_main_writes_html_report(self, mock_run_checks):
        mock_run_checks.return_value = [
            CheckResult("A", "https://example.com/a", "ok", "HTTP 200", 200, "https://example.com/a"),
            CheckResult("B", "https://example.com/b", "blocked", "HTTP 403", 403, "https://example.com/b"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            bookmark_file = Path(tmpdir) / "bookmarks.html"
            output_file = Path(tmpdir) / "report.html"
            bookmark_file.write_text('<a href="https://example.com/a">A</a>', encoding="utf-8")

            exit_code = main(["check", str(bookmark_file), "--format", "html", "--output", str(output_file)])
            content = output_file.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("Bookmark Check Report", content)
        self.assertIn("https://example.com/b", content)

    def test_diff_command_writes_json_and_reports_regressions(self):
        previous_payload = [
            {
                "title": "A",
                "url": "https://example.com/a",
                "status": "ok",
                "status_code": 200,
                "detail": "HTTP 200",
                "final_url": "https://example.com/a",
            }
        ]
        current_payload = [
            {
                "title": "A",
                "url": "https://example.com/a",
                "status": "client_error",
                "status_code": 404,
                "detail": "HTTP 404",
                "final_url": "https://example.com/a",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            previous_file = Path(tmpdir) / "previous.json"
            current_file = Path(tmpdir) / "current.json"
            output_file = Path(tmpdir) / "diff.json"
            previous_file.write_text(json.dumps(previous_payload), encoding="utf-8")
            current_file.write_text(json.dumps(current_payload), encoding="utf-8")

            exit_code = main(
                ["diff", str(previous_file), str(current_file), "--format", "json", "--output", str(output_file)]
            )
            payload = json.loads(output_file.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["summary"]["regressions"], 1)
        self.assertEqual(payload["entries"][0]["current_status"], "client_error")

    def test_main_returns_argument_error_for_missing_input_file(self):
        exit_code = main(["check", "/tmp/does-not-exist-bookmarks.html"])

        self.assertEqual(exit_code, 2)

    def test_diff_command_returns_argument_error_for_missing_input_file(self):
        exit_code = main(["diff", "/tmp/missing-previous.json", "/tmp/missing-current.json"])

        self.assertEqual(exit_code, 2)
