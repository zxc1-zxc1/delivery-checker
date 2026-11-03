import time

from .checkers import check_disk, check_http, check_port
from .models import ErrorType, InspectionStatus


RETRYABLE_ERRORS = {
    ErrorType.TIMEOUT,
    ErrorType.CONNECTION,
}


def run_with_retry(
    check_function,
    max_attempts=1,
    retry_delay=0.2,
    **check_kwargs,
):
    """执行检查，记录总耗时，并对可重试错误进行重试。"""

    started_at = time.perf_counter()
    attempts = 0

    while True:
        attempts += 1
        result = check_function(**check_kwargs)
        result.attempts = attempts

        should_retry = (
            result.status == InspectionStatus.FAIL
            and result.error_type in RETRYABLE_ERRORS
            and attempts < max_attempts
        )

        if not should_retry:
            result.duration_ms = round(
                (time.perf_counter() - started_at) * 1000,
                2,
            )
            return result

        time.sleep(retry_delay)


def run_checks(config) -> list[dict]:
    """根据配置依次执行所有巡检任务。"""

    results = []

    disk_config = config.get("disk", {})
    disk_result = run_with_retry(
        check_disk,
        path=disk_config.get("path"),
        min_free_gb=disk_config.get("min_free_gb", 10),
    )
    results.append(disk_result.to_dict())

    for port_config in config["ports"]:
        port_result = run_with_retry(
            check_port,
            host=port_config["host"],
            port=port_config["port"],
            timeout=port_config.get("timeout", 3),
        )
        results.append(port_result.to_dict())

    for http_config in config["http_checks"]:
        http_result = run_with_retry(
            check_http,
            url=http_config["url"],
            timeout=http_config.get("timeout", 5),
        )
        results.append(http_result.to_dict())

    return results