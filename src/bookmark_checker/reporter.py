from __future__ import annotations

import csv
import html
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from bookmark_checker.config import (
    DEFAULT_CSV_OUTPUT,
    DEFAULT_DIFF_CSV_OUTPUT,
    DEFAULT_DIFF_HTML_OUTPUT,
    DEFAULT_DIFF_JSON_OUTPUT,
    DEFAULT_HTML_OUTPUT,
    DEFAULT_JSON_OUTPUT,
)
from bookmark_checker.models import CheckResult, DiffEntry, DiffSummary


def resolve_output_path(output: str | None, output_format: str) -> Path:
    if output:
        return Path(output)
    if output_format == "html":
        return Path(DEFAULT_HTML_OUTPUT)
    if output_format == "json":
        return Path(DEFAULT_JSON_OUTPUT)
    return Path(DEFAULT_CSV_OUTPUT)


def write_results(results: Iterable[CheckResult], output_path: str | Path, output_format: str) -> Path:
    path = Path(output_path)
    materialized = list(results)

    if output_format == "html":
        write_html_report(materialized, path)
    elif output_format == "json":
        write_json(materialized, path)
    else:
        write_csv(materialized, path)

    return path


def write_csv(results: Iterable[CheckResult], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["title", "url", "status", "status_code", "detail", "final_url", "is_problem", "is_uncertain"]
        )

        for result in results:
            writer.writerow(
                [
                    result.title,
                    result.url,
                    result.status,
                    result.status_code or "",
                    result.detail,
                    result.final_url,
                    "yes" if result.is_problem else "no",
                    "yes" if result.is_uncertain else "no",
                ]
            )


def write_html_report(results: list[CheckResult], output_path: Path) -> None:
    counter = Counter(result.status for result in results)
    problem_count = sum(1 for result in results if result.is_problem)
    uncertain_count = sum(1 for result in results if result.is_uncertain)
    rows = []
    for result in results:
        rows.append(
            "<tr>"
            f"<td>{escape(result.title)}</td>"
            f"<td><a href=\"{escape(result.url)}\">{escape(result.url)}</a></td>"
            f"<td><span class=\"status {escape(result.status)}\">{escape(result.status)}</span></td>"
            f"<td>{escape(str(result.status_code or ''))}</td>"
            f"<td>{escape(result.detail)}</td>"
            f"<td>{escape(result.final_url)}</td>"
            "</tr>"
        )

    summary_cards = [
        summary_card("总链接数", str(len(results))),
        summary_card("明确异常", str(problem_count)),
        summary_card("可能误伤", str(uncertain_count)),
        summary_card("状态种类", str(len(counter))),
    ]
    breakdown_items = "".join(
        f"<li><span>{escape(status)}</span><strong>{count}</strong></li>" for status, count in sorted(counter.items())
    )

    document = render_page(
        title="Bookmark Check Report",
        subtitle="书签检查报告",
        summary_cards="".join(summary_cards),
        content="""
            <section class="panel">
              <h2>状态统计</h2>
              <ul class="stats-list">{breakdown_items}</ul>
            </section>
            <section class="panel">
              <h2>检查结果</h2>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>URL</th>
                      <th>Status</th>
                      <th>Status Code</th>
                      <th>Detail</th>
                      <th>Final URL</th>
                    </tr>
                  </thead>
                  <tbody>{rows}</tbody>
                </table>
              </div>
            </section>
        """.format(breakdown_items=breakdown_items, rows="".join(rows)),
    )

    output_path.write_text(document, encoding="utf-8")


def write_json(results: Iterable[CheckResult], output_path: Path) -> None:
    payload = [
        {
            "title": result.title,
            "url": result.url,
            "status": result.status,
            "status_code": result.status_code,
            "detail": result.detail,
            "final_url": result.final_url,
            "is_problem": result.is_problem,
            "is_uncertain": result.is_uncertain,
        }
        for result in results
    ]

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def load_results(input_path: str | Path) -> list[CheckResult]:
    path = Path(input_path)

    if path.suffix.lower() == ".json":
        return load_results_json(path)

    return load_results_csv(path)


def load_results_csv(input_path: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            results.append(
                CheckResult(
                    title=row.get("title", ""),
                    url=row.get("url", ""),
                    status=row.get("status", ""),
                    detail=row.get("detail", ""),
                    status_code=parse_status_code(row.get("status_code", "")),
                    final_url=row.get("final_url", ""),
                )
            )

    return results


def load_results_json(input_path: Path) -> list[CheckResult]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    results: list[CheckResult] = []

    for item in payload:
        results.append(
            CheckResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                status=item.get("status", ""),
                detail=item.get("detail", ""),
                status_code=parse_status_code(item.get("status_code")),
                final_url=item.get("final_url", ""),
            )
        )

    return results


def resolve_diff_output_path(output: str | None, output_format: str) -> Path:
    if output:
        return Path(output)
    if output_format == "html":
        return Path(DEFAULT_DIFF_HTML_OUTPUT)
    if output_format == "json":
        return Path(DEFAULT_DIFF_JSON_OUTPUT)
    return Path(DEFAULT_DIFF_CSV_OUTPUT)


def write_diff_results(
    entries: list[DiffEntry],
    summary: DiffSummary,
    output_path: str | Path,
    output_format: str,
) -> Path:
    path = Path(output_path)

    if output_format == "html":
        write_diff_html(entries, summary, path)
    elif output_format == "json":
        write_diff_json(entries, summary, path)
    else:
        write_diff_csv(entries, path)

    return path


def write_diff_csv(entries: Iterable[DiffEntry], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "title",
                "url",
                "change_type",
                "previous_status",
                "current_status",
                "previous_status_code",
                "current_status_code",
                "previous_detail",
                "current_detail",
            ]
        )
        for entry in entries:
            writer.writerow(
                [
                    entry.title,
                    entry.url,
                    entry.change_type,
                    entry.previous_status,
                    entry.current_status,
                    entry.previous_status_code or "",
                    entry.current_status_code or "",
                    entry.previous_detail,
                    entry.current_detail,
                ]
            )


def write_diff_json(entries: list[DiffEntry], summary: DiffSummary, output_path: Path) -> None:
    payload = {
        "summary": {
            "total_previous": summary.total_previous,
            "total_current": summary.total_current,
            "added": summary.added,
            "removed": summary.removed,
            "changed": summary.changed,
            "unchanged": summary.unchanged,
            "regressions": summary.regressions,
            "recoveries": summary.recoveries,
        },
        "entries": [
            {
                "title": entry.title,
                "url": entry.url,
                "change_type": entry.change_type,
                "previous_status": entry.previous_status,
                "current_status": entry.current_status,
                "previous_status_code": entry.previous_status_code,
                "current_status_code": entry.current_status_code,
                "previous_detail": entry.previous_detail,
                "current_detail": entry.current_detail,
            }
            for entry in entries
        ],
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_diff_html(entries: list[DiffEntry], summary: DiffSummary, output_path: Path) -> None:
    rows = []
    for entry in entries:
        rows.append(
            "<tr>"
            f"<td>{escape(entry.title)}</td>"
            f"<td><a href=\"{escape(entry.url)}\">{escape(entry.url)}</a></td>"
            f"<td><span class=\"status {escape(entry.change_type)}\">{escape(entry.change_type)}</span></td>"
            f"<td>{escape(entry.previous_status)}</td>"
            f"<td>{escape(entry.current_status)}</td>"
            f"<td>{escape(entry.previous_detail)}</td>"
            f"<td>{escape(entry.current_detail)}</td>"
            "</tr>"
        )

    summary_cards = [
        summary_card("旧结果数", str(summary.total_previous)),
        summary_card("新结果数", str(summary.total_current)),
        summary_card("回归", str(summary.regressions)),
        summary_card("恢复", str(summary.recoveries)),
    ]
    breakdown_items = "".join(
        [
            f"<li><span>added</span><strong>{summary.added}</strong></li>",
            f"<li><span>removed</span><strong>{summary.removed}</strong></li>",
            f"<li><span>changed</span><strong>{summary.changed}</strong></li>",
            f"<li><span>unchanged</span><strong>{summary.unchanged}</strong></li>",
        ]
    )

    document = render_page(
        title="Bookmark Check Diff",
        subtitle="书签检查差异报告",
        summary_cards="".join(summary_cards),
        content="""
            <section class="panel">
              <h2>变化统计</h2>
              <ul class="stats-list">{breakdown_items}</ul>
            </section>
            <section class="panel">
              <h2>变化明细</h2>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>URL</th>
                      <th>Change</th>
                      <th>Previous Status</th>
                      <th>Current Status</th>
                      <th>Previous Detail</th>
                      <th>Current Detail</th>
                    </tr>
                  </thead>
                  <tbody>{rows}</tbody>
                </table>
              </div>
            </section>
        """.format(breakdown_items=breakdown_items, rows="".join(rows)),
    )

    output_path.write_text(document, encoding="utf-8")


def format_summary(results: list[CheckResult], output_path: str | Path) -> str:
    counter = Counter(result.status for result in results)
    problem_count = sum(1 for result in results if result.is_problem)
    uncertain_count = sum(1 for result in results if result.is_uncertain)

    lines = [
        "检查完成",
        f"总链接数: {len(results)}",
        f"明确异常: {problem_count}",
        f"可能误伤: {uncertain_count}",
        f"结果文件: {Path(output_path).resolve()}",
    ]

    if counter:
        lines.append("状态统计:")
        for status, count in sorted(counter.items()):
            lines.append(f"  - {status}: {count}")

    return "\n".join(lines)


def format_diff_summary(summary: DiffSummary, output_path: str | Path) -> str:
    lines = [
        "对比完成",
        f"旧结果数: {summary.total_previous}",
        f"新结果数: {summary.total_current}",
        f"新增链接: {summary.added}",
        f"移除链接: {summary.removed}",
        f"变化链接: {summary.changed}",
        f"未变化链接: {summary.unchanged}",
        f"回归数量: {summary.regressions}",
        f"恢复数量: {summary.recoveries}",
        f"结果文件: {Path(output_path).resolve()}",
    ]
    return "\n".join(lines)


def parse_status_code(value: object) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def summary_card(label: str, value: str) -> str:
    return (
        "<article class=\"card\">"
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(value)}</strong>"
        "</article>"
    )


def render_page(title: str, subtitle: str, summary_cards: str, content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3efe6;
      --panel: rgba(255, 252, 245, 0.9);
      --ink: #1e2430;
      --muted: #5f6b7a;
      --line: rgba(30, 36, 48, 0.12);
      --accent: #0b6e4f;
      --warn: #d17a22;
      --danger: #b03a2e;
      --chip: #e8efe8;
      --shadow: 0 18px 60px rgba(32, 41, 54, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(11, 110, 79, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(209, 122, 34, 0.16), transparent 32%),
        linear-gradient(180deg, #f8f3ea 0%, var(--bg) 100%);
    }}
    .shell {{
      width: min(1200px, calc(100% - 32px));
      margin: 32px auto 48px;
    }}
    .hero {{
      padding: 28px 30px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(255,255,255,0.7), rgba(255,249,240,0.92));
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }}
    .hero h1 {{
      margin: 0;
      font-size: clamp(28px, 4vw, 42px);
      line-height: 1.05;
      letter-spacing: -0.04em;
    }}
    .hero p {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 16px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 18px 0 0;
    }}
    .card {{
      padding: 18px;
      border-radius: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
    }}
    .card span {{
      display: block;
      font-size: 13px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .card strong {{
      display: block;
      margin-top: 8px;
      font-size: 28px;
      letter-spacing: -0.03em;
    }}
    .grid {{
      display: grid;
      gap: 18px;
      margin-top: 22px;
    }}
    .panel {{
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .panel h2 {{
      margin: 0 0 16px;
      font-size: 20px;
      letter-spacing: -0.03em;
    }}
    .stats-list {{
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }}
    .stats-list li {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 16px;
      border-radius: 16px;
      background: #fff;
      border: 1px solid var(--line);
    }}
    .table-wrap {{
      overflow: auto;
      border-radius: 16px;
      border: 1px solid var(--line);
      background: #fff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 920px;
    }}
    th, td {{
      padding: 14px 16px;
      text-align: left;
      vertical-align: top;
      border-bottom: 1px solid var(--line);
      font-size: 14px;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #fcfaf5;
      z-index: 1;
    }}
    td a {{
      color: #145da0;
      text-decoration: none;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 600;
      background: var(--chip);
      color: var(--ink);
    }}
    .status.ok, .status.recovered {{
      background: rgba(11, 110, 79, 0.14);
      color: var(--accent);
    }}
    .status.blocked, .status.changed {{
      background: rgba(209, 122, 34, 0.14);
      color: var(--warn);
    }}
    .status.client_error, .status.server_error, .status.timeout,
    .status.connection_error, .status.ssl_error, .status.invalid_url,
    .status.too_many_redirects, .status.request_error, .status.added,
    .status.removed {{
      background: rgba(176, 58, 46, 0.14);
      color: var(--danger);
    }}
    @media (max-width: 720px) {{
      .shell {{ width: min(100% - 18px, 1200px); margin-top: 18px; }}
      .hero, .panel {{ padding: 18px; border-radius: 18px; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>{escape(title)}</h1>
      <p>{escape(subtitle)}</p>
      <div class="cards">{summary_cards}</div>
    </section>
    <section class="grid">
      {content}
    </section>
  </main>
</body>
</html>
"""
