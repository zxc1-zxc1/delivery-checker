import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .checkers import check_disk, check_http, check_mysql, check_port
from .models import (
    ErrorType,
    InspectionResult,
    InspectionStatus,
)

RETRYABLE_ERRORS = {
    ErrorType.TIMEOUT,
    ErrorType.CONNECTION,
}

CheckFunction = Callable[..., InspectionResult]
NetworkTask = tuple[str, str, CheckFunction, dict[str, Any]]


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


def _run_safely(check_function, item, target, **check_kwargs):
    """执行单项任务，避免未预期异常中断整个巡检。"""

    try:
        return run_with_retry(check_function, **check_kwargs)

    except Exception as exc:
        return InspectionResult(
            item=item,
            target=target,
            status=InspectionStatus.FAIL,
            message=f"检查执行异常：{exc}",
            error_type=ErrorType.UNEXPECTED,
        )


def run_checks(config) -> list[dict]:
    """执行磁盘检查，并发执行网络检查，保持结果顺序稳定。"""

    results = []

    disk_config = config.get("disk", {})
    disk_result = run_with_retry(
        check_disk,
        path=disk_config.get("path"),
        min_free_gb=disk_config.get("min_free_gb", 10),
    )
    results.append(disk_result.to_dict())

    network_tasks: list[NetworkTask] = []

    for port_config in config["ports"]:
        host = port_config["host"]
        port = port_config["port"]

        network_tasks.append(
            (
                "tcp_port",
                f"{host}:{port}",
                check_port,
                {
                    "max_attempts": port_config.get("max_attempts", 1),
                    "retry_delay": port_config.get("retry_delay", 0.2),
                    "host": host,
                    "port": port,
                    "timeout": port_config.get("timeout", 3),
                },
            )
        )

    for http_config in config["http_checks"]:
        url = http_config["url"]

        network_tasks.append(
            (
                "http_health",
                url,
                check_http,
                {
                    "max_attempts": http_config.get("max_attempts", 1),
                    "retry_delay": http_config.get("retry_delay", 0.2),
                    "url": url,
                    "timeout": http_config.get("timeout", 5),
                },
            )
        )

    for mysql_config in config.get("mysql_checks", []):
        host = mysql_config["host"]
        port = mysql_config.get("port", 3306)
        password_env = mysql_config.get(
            "password_env",
            "DELIVERY_CHECKER_MYSQL_PASSWORD",
        )

        network_tasks.append(
            (
                "mysql_health",
                f"{host}:{port}",
                check_mysql,
                {
                    "max_attempts": mysql_config.get("max_attempts", 1),
                    "retry_delay": mysql_config.get("retry_delay", 0.2),
                    "host": host,
                    "port": port,
                    "user": mysql_config["user"],
                    "password": os.environ.get(password_env, ""),
                    "database": mysql_config.get("database"),
                    "timeout": mysql_config.get("timeout", 5),
                },
            )
        )

    if network_tasks:
        with ThreadPoolExecutor(
            max_workers=min(4, len(network_tasks))
        ) as executor:
            futures = [
                executor.submit(
                    _run_safely,
                    check_function,
                    item,
                    target,
                    **check_kwargs,
                )
                for item, target, check_function, check_kwargs in network_tasks
            ]

            for future in futures:
                results.append(future.result().to_dict())

    return results
