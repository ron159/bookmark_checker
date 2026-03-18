import tempfile
import unittest
from pathlib import Path

from tests import _bootstrap
from bookmark_checker.models import Bookmark
from bookmark_checker.parser import domain_matches, filter_bookmarks, load_bookmarks


class ParserTests(unittest.TestCase):
    def test_load_bookmarks_skips_duplicates_and_empty_href(self):
        html = """
        <html><body>
          <a href="https://example.com">Example</a>
          <a href="https://example.com">Duplicate</a>
          <a href="">Empty</a>
          <a>No href</a>
        </body></html>
        """

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bookmarks.html"
            path.write_text(html, encoding="utf-8")
            bookmarks = load_bookmarks(path)

        self.assertEqual(bookmarks, [Bookmark(title="Example", url="https://example.com")])

    def test_domain_matches_supports_subdomains(self):
        self.assertTrue(domain_matches("sub.example.com", {"example.com"}))
        self.assertFalse(domain_matches("example.org", {"example.com"}))

    def test_filter_bookmarks_applies_include_and_exclude_domains(self):
        bookmarks = [
            Bookmark("A", "https://example.com/a"),
            Bookmark("B", "https://sub.example.com/b"),
            Bookmark("C", "https://other.com/c"),
        ]

        filtered = filter_bookmarks(bookmarks, include_domains={"example.com"}, exclude_domains={"sub.example.com"})

        self.assertEqual(filtered, [Bookmark("A", "https://example.com/a")])
