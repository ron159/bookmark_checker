from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable
from urllib.parse import urlparse

import requests

from bookmark_checker.config import CHECKABLE_SCHEMES
from bookmark_checker.models import Bookmark, CheckOptions, CheckResult


def classify_http_status(bookmark: Bookmark, response: requests.Response) -> CheckResult:
    code = response.status_code
    detail = f"HTTP {code}"

    if code < 400:
        status = "ok"
    elif code in (401, 403):
        status = "blocked"
    elif code < 500:
        status = "client_error"
    else:
        status = "server_error"

    return CheckResult(
        title=bookmark.title,
        url=bookmark.url,
        status=status,
        detail=detail,
        status_code=code,
        final_url=response.url,
    )


def check_bookmark(bookmark: Bookmark, options: CheckOptions) -> CheckResult:
    parsed = urlparse(bookmark.url)

    if not parsed.scheme:
        return CheckResult(bookmark.title, bookmark.url, "invalid_url", "缺少 URL scheme")

    if parsed.scheme.lower() not in CHECKABLE_SCHEMES:
        return CheckResult(
            bookmark.title,
            bookmark.url,
            "skipped_unsupported_scheme",
            f"不支持的 scheme: {parsed.scheme}",
        )

    headers = {"User-Agent": options.user_agent}
    attempts = max(options.retries, 0) + 1
    last_result: CheckResult | None = None

    for attempt in range(1, attempts + 1):
        try:
            with requests.get(
                bookmark.url,
                headers=headers,
                timeout=options.timeout,
                allow_redirects=options.follow_redirects,
                proxies=options.proxies,
                stream=True,
            ) as response:
                return classify_http_status(bookmark, response)
        except requests.exceptions.Timeout:
            last_result = CheckResult(
                bookmark.title,
                bookmark.url,
                "timeout",
                f"请求超时 (attempt {attempt}/{attempts})",
            )
        except requests.exceptions.SSLError as exc:
            return CheckResult(bookmark.title, bookmark.url, "ssl_error", str(exc))
        except requests.exceptions.InvalidURL as exc:
            return CheckResult(bookmark.title, bookmark.url, "invalid_url", str(exc))
        except requests.exceptions.TooManyRedirects:
            return CheckResult(bookmark.title, bookmark.url, "too_many_redirects", "重定向次数过多")
        except requests.exceptions.ConnectionError as exc:
            last_result = CheckResult(
                bookmark.title,
                bookmark.url,
                "connection_error",
                f"{exc} (attempt {attempt}/{attempts})",
            )
        except requests.exceptions.RequestException as exc:
            last_result = CheckResult(
                bookmark.title,
                bookmark.url,
                "request_error",
                f"{exc} (attempt {attempt}/{attempts})",
            )

    return last_result or CheckResult(bookmark.title, bookmark.url, "request_error", "未知请求错误")


def run_checks(bookmarks: Iterable[Bookmark], options: CheckOptions) -> list[CheckResult]:
    results: list[CheckResult] = []

    with ThreadPoolExecutor(max_workers=max(options.workers, 1)) as executor:
        futures = {executor.submit(check_bookmark, bookmark, options): bookmark for bookmark in bookmarks}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if options.verbose:
                print(f"[{result.status}] {result.url}")

    results.sort(key=lambda item: (item.status, item.url))
    return results
