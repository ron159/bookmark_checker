import unittest
from unittest.mock import MagicMock, patch

import requests

from tests import _bootstrap
from bookmark_checker.checker import check_bookmark
from bookmark_checker.models import Bookmark, CheckOptions


def build_response(status_code: int, url: str):
    response = MagicMock()
    response.status_code = status_code
    response.url = url

    context_manager = MagicMock()
    context_manager.__enter__.return_value = response
    context_manager.__exit__.return_value = False
    return context_manager


def build_options(**kwargs):
    defaults = {
        "workers": 4,
        "timeout": 2,
        "retries": 1,
        "user_agent": "test-agent",
        "follow_redirects": True,
        "proxies": None,
        "verbose": False,
    }
    defaults.update(kwargs)
    return CheckOptions(**defaults)


class CheckerTests(unittest.TestCase):
    @patch("requests.get")
    def test_check_bookmark_classifies_http_results(self, mock_get):
        mock_get.side_effect = [
            build_response(200, "https://example.com/ok"),
            build_response(403, "https://example.com/forbidden"),
            build_response(404, "https://example.com/missing"),
        ]

        ok_result = check_bookmark(Bookmark("OK", "https://example.com/ok"), build_options())
        blocked_result = check_bookmark(Bookmark("Forbidden", "https://example.com/forbidden"), build_options())
        missing_result = check_bookmark(Bookmark("Missing", "https://example.com/missing"), build_options())

        self.assertEqual(ok_result.status, "ok")
        self.assertEqual(blocked_result.status, "blocked")
        self.assertEqual(missing_result.status, "client_error")

    @patch("requests.get", side_effect=[requests.exceptions.Timeout, build_response(200, "https://example.com/final")])
    def test_check_bookmark_retries_timeout(self, mock_get):
        result = check_bookmark(Bookmark("Retry", "https://example.com/retry"), build_options(retries=1))

        self.assertEqual(result.status, "ok")
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get", side_effect=requests.exceptions.Timeout)
    def test_check_bookmark_returns_timeout_after_all_retries(self, mock_get):
        result = check_bookmark(Bookmark("Slow", "https://example.com/slow"), build_options(retries=2))

        self.assertEqual(result.status, "timeout")
        self.assertIn("attempt 3/3", result.detail)

    def test_check_bookmark_marks_unsupported_scheme_as_skipped(self):
        result = check_bookmark(Bookmark("Mail", "mailto:test@example.com"), build_options())

        self.assertEqual(result.status, "skipped_unsupported_scheme")
