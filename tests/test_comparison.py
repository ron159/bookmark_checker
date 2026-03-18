import unittest

from tests import _bootstrap
from bookmark_checker.comparison import compare_results
from bookmark_checker.models import CheckResult


class ComparisonTests(unittest.TestCase):
    def test_compare_results_tracks_changed_added_removed_and_recovery(self):
        previous = [
            CheckResult("Stable", "https://example.com/stable", "ok", "HTTP 200", 200, "https://example.com/stable"),
            CheckResult("Broken", "https://example.com/broken", "client_error", "HTTP 404", 404, "https://example.com/broken"),
            CheckResult("Removed", "https://example.com/removed", "ok", "HTTP 200", 200, "https://example.com/removed"),
        ]
        current = [
            CheckResult("Stable", "https://example.com/stable", "blocked", "HTTP 403", 403, "https://example.com/stable"),
            CheckResult("Broken", "https://example.com/broken", "ok", "HTTP 200", 200, "https://example.com/broken"),
            CheckResult("Added", "https://example.com/added", "ok", "HTTP 200", 200, "https://example.com/added"),
        ]

        entries, summary = compare_results(previous, current)

        self.assertEqual(summary.added, 1)
        self.assertEqual(summary.removed, 1)
        self.assertEqual(summary.changed, 2)
        self.assertEqual(summary.unchanged, 0)
        self.assertEqual(summary.regressions, 1)
        self.assertEqual(summary.recoveries, 1)
        self.assertEqual({entry.change_type for entry in entries}, {"added", "removed", "changed"})
