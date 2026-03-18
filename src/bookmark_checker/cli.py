from __future__ import annotations

import argparse
import json

from bookmark_checker.checker import run_checks
from bookmark_checker.comparison import compare_results
from bookmark_checker.config import DEFAULT_RETRIES, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_WORKERS
from bookmark_checker.models import CheckOptions
from bookmark_checker.parser import filter_bookmarks, load_bookmarks
from bookmark_checker.reporter import (
    format_diff_summary,
    format_summary,
    load_results,
    resolve_diff_output_path,
    resolve_output_path,
    write_diff_results,
    write_results,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bookmark-checker", description="检查浏览器导出的 HTML 书签是否可访问")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="检查书签文件中的链接")
    check_parser.add_argument("bookmark_file", help="Chrome/Edge 等浏览器导出的书签 HTML 文件路径")
    check_parser.add_argument("-o", "--output", help="输出文件路径")
    check_parser.add_argument(
        "--format",
        choices=("csv", "json", "html"),
        default="csv",
        help="输出格式，默认: csv",
    )
    check_parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"并发数，默认: {DEFAULT_WORKERS}",
    )
    check_parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"单个请求超时时间（秒），默认: {DEFAULT_TIMEOUT}",
    )
    check_parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"网络异常时的重试次数，默认: {DEFAULT_RETRIES}",
    )
    check_parser.add_argument("--proxy", help="可选代理，例如 socks5://127.0.0.1:7891")
    check_parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="请求头中的 User-Agent，可按需覆盖",
    )
    check_parser.add_argument(
        "--follow-redirects",
        dest="follow_redirects",
        action="store_true",
        default=True,
        help="跟随重定向，默认开启",
    )
    check_parser.add_argument(
        "--no-follow-redirects",
        dest="follow_redirects",
        action="store_false",
        help="不跟随重定向",
    )
    check_parser.add_argument(
        "--include-domain",
        action="append",
        default=[],
        help="仅检查指定域名，可重复传入",
    )
    check_parser.add_argument(
        "--exclude-domain",
        action="append",
        default=[],
        help="跳过指定域名，可重复传入",
    )
    check_parser.add_argument(
        "--only-problems",
        action="store_true",
        help="仅将问题链接写入输出文件",
    )
    check_parser.add_argument(
        "--verbose",
        action="store_true",
        help="输出每个链接的检查结果",
    )

    diff_parser = subparsers.add_parser("diff", help="对比两次检查结果")
    diff_parser.add_argument("previous_file", help="旧结果文件，支持 csv/json")
    diff_parser.add_argument("current_file", help="新结果文件，支持 csv/json")
    diff_parser.add_argument("-o", "--output", help="输出文件路径")
    diff_parser.add_argument(
        "--format",
        choices=("csv", "json", "html"),
        default="html",
        help="输出格式，默认: html",
    )

    return parser


def build_proxies(proxy: str | None) -> dict[str, str] | None:
    if not proxy:
        return None
    return {"http": proxy, "https": proxy}


def run_check_command(args: argparse.Namespace) -> int:
    try:
        bookmarks = load_bookmarks(args.bookmark_file)
    except FileNotFoundError:
        print(f"书签文件不存在: {args.bookmark_file}")
        return 2
    except OSError as exc:
        print(f"读取书签文件失败: {exc}")
        return 2

    include_domains = {value.lower() for value in args.include_domain if value.strip()}
    exclude_domains = {value.lower() for value in args.exclude_domain if value.strip()}
    bookmarks = filter_bookmarks(bookmarks, include_domains=include_domains or None, exclude_domains=exclude_domains or None)

    if not bookmarks:
        print("未在书签文件中找到可检查的链接")
        return 2

    options = CheckOptions(
        workers=args.workers,
        timeout=args.timeout,
        retries=args.retries,
        user_agent=args.user_agent,
        follow_redirects=args.follow_redirects,
        proxies=build_proxies(args.proxy),
        verbose=args.verbose,
    )
    results = run_checks(bookmarks, options)
    output_rows = [result for result in results if result.is_problem or result.is_uncertain] if args.only_problems else results
    output_path = resolve_output_path(args.output, args.format)
    write_results(output_rows, output_path, args.format)
    print(format_summary(results, output_path))
    return 1 if any(result.is_problem for result in results) else 0


def run_diff_command(args: argparse.Namespace) -> int:
    try:
        previous = load_results(args.previous_file)
        current = load_results(args.current_file)
    except FileNotFoundError as exc:
        print(f"结果文件不存在: {exc.filename}")
        return 2
    except OSError as exc:
        print(f"读取结果文件失败: {exc}")
        return 2
    except ValueError as exc:
        print(f"结果文件格式不正确: {exc}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"JSON 结果文件解析失败: {exc}")
        return 2

    entries, summary = compare_results(previous, current)
    output_path = resolve_diff_output_path(args.output, args.format)
    write_diff_results(entries, summary, output_path, args.format)
    print(format_diff_summary(summary, output_path))
    return 1 if summary.regressions > 0 else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return run_check_command(args)
    if args.command == "diff":
        return run_diff_command(args)

    parser.print_help()
    return 2
