DEFAULT_TIMEOUT = 10.0
DEFAULT_WORKERS = 20
DEFAULT_RETRIES = 1
DEFAULT_CSV_OUTPUT = "bookmark_check_results.csv"
DEFAULT_JSON_OUTPUT = "bookmark_check_results.json"
DEFAULT_HTML_OUTPUT = "bookmark_check_results.html"
DEFAULT_DIFF_CSV_OUTPUT = "bookmark_check_diff.csv"
DEFAULT_DIFF_JSON_OUTPUT = "bookmark_check_diff.json"
DEFAULT_DIFF_HTML_OUTPUT = "bookmark_check_diff.html"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
CHECKABLE_SCHEMES = {"http", "https"}
PROBLEM_STATUSES = {
    "client_error",
    "server_error",
    "timeout",
    "connection_error",
    "ssl_error",
    "invalid_url",
    "too_many_redirects",
    "request_error",
}
UNCERTAIN_STATUSES = {"blocked"}
