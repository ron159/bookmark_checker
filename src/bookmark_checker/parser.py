from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from bookmark_checker.models import Bookmark


def load_bookmarks(path: str | Path) -> list[Bookmark]:
    bookmark_path = Path(path)
    with bookmark_path.open("r", encoding="utf-8") as handle:
        soup = BeautifulSoup(handle, "html.parser")

    bookmarks: list[Bookmark] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a"):
        url = (link.get("href") or "").strip()
        title = link.get_text(strip=True) or "(无标题)"

        if not url or url in seen_urls:
            continue

        seen_urls.add(url)
        bookmarks.append(Bookmark(title=title, url=url))

    return bookmarks


def filter_bookmarks(
    bookmarks: list[Bookmark],
    include_domains: set[str] | None = None,
    exclude_domains: set[str] | None = None,
) -> list[Bookmark]:
    filtered: list[Bookmark] = []

    for bookmark in bookmarks:
        hostname = urlparse(bookmark.url).hostname or ""

        if include_domains and not domain_matches(hostname, include_domains):
            continue

        if exclude_domains and domain_matches(hostname, exclude_domains):
            continue

        filtered.append(bookmark)

    return filtered


def domain_matches(hostname: str, domains: set[str]) -> bool:
    normalized_host = hostname.lower().strip(".")

    for domain in domains:
        normalized_domain = domain.lower().strip(".")
        if normalized_host == normalized_domain or normalized_host.endswith(f".{normalized_domain}"):
            return True

    return False
