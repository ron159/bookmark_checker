from __future__ import annotations

from bookmark_checker.models import CheckResult, DiffEntry, DiffSummary


def compare_results(previous: list[CheckResult], current: list[CheckResult]) -> tuple[list[DiffEntry], DiffSummary]:
    previous_by_url = {result.url: result for result in previous}
    current_by_url = {result.url: result for result in current}

    entries: list[DiffEntry] = []
    added = removed = changed = unchanged = regressions = recoveries = 0

    for url in sorted(set(previous_by_url) | set(current_by_url)):
        previous_result = previous_by_url.get(url)
        current_result = current_by_url.get(url)

        if previous_result is None and current_result is not None:
            added += 1
            if current_result.is_problem or current_result.is_uncertain:
                regressions += 1
            entries.append(
                DiffEntry(
                    url=url,
                    title=current_result.title,
                    change_type="added",
                    previous_status="missing",
                    current_status=current_result.status,
                    current_status_code=current_result.status_code,
                    current_detail=current_result.detail,
                )
            )
            continue

        if previous_result is not None and current_result is None:
            removed += 1
            entries.append(
                DiffEntry(
                    url=url,
                    title=previous_result.title,
                    change_type="removed",
                    previous_status=previous_result.status,
                    current_status="missing",
                    previous_status_code=previous_result.status_code,
                    previous_detail=previous_result.detail,
                )
            )
            continue

        assert previous_result is not None
        assert current_result is not None

        if results_match(previous_result, current_result):
            unchanged += 1
            continue

        changed += 1
        previous_bad = previous_result.is_problem or previous_result.is_uncertain
        current_bad = current_result.is_problem or current_result.is_uncertain

        if not previous_bad and current_bad:
            regressions += 1
        elif previous_bad and not current_bad:
            recoveries += 1

        entries.append(
            DiffEntry(
                url=url,
                title=current_result.title or previous_result.title,
                change_type="changed",
                previous_status=previous_result.status,
                current_status=current_result.status,
                previous_status_code=previous_result.status_code,
                current_status_code=current_result.status_code,
                previous_detail=previous_result.detail,
                current_detail=current_result.detail,
            )
        )

    summary = DiffSummary(
        total_previous=len(previous),
        total_current=len(current),
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
        regressions=regressions,
        recoveries=recoveries,
    )
    return entries, summary


def results_match(previous: CheckResult, current: CheckResult) -> bool:
    return (
        previous.status == current.status
        and previous.status_code == current.status_code
        and previous.final_url == current.final_url
    )
