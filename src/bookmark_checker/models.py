from __future__ import annotations

from dataclasses import dataclass

from bookmark_checker.config import PROBLEM_STATUSES, UNCERTAIN_STATUSES


@dataclass(frozen=True)
class Bookmark:
    title: str
    url: str


@dataclass(frozen=True)
class CheckResult:
    title: str
    url: str
    status: str
    detail: str
    status_code: int | None = None
    final_url: str = ""

    @property
    def is_problem(self) -> bool:
        return self.status in PROBLEM_STATUSES

    @property
    def is_uncertain(self) -> bool:
        return self.status in UNCERTAIN_STATUSES


@dataclass(frozen=True)
class CheckOptions:
    workers: int
    timeout: float
    retries: int
    user_agent: str
    follow_redirects: bool
    proxies: dict[str, str] | None
    verbose: bool


@dataclass(frozen=True)
class DiffEntry:
    url: str
    title: str
    change_type: str
    previous_status: str
    current_status: str
    previous_status_code: int | None = None
    current_status_code: int | None = None
    previous_detail: str = ""
    current_detail: str = ""


@dataclass(frozen=True)
class DiffSummary:
    total_previous: int
    total_current: int
    added: int
    removed: int
    changed: int
    unchanged: int
    regressions: int
    recoveries: int
