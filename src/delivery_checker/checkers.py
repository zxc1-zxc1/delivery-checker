import shutil
import socket
import time
from pathlib import Path
from urllib import error, request

import pymysql

from .models import ErrorType, InspectionResult, InspectionStatus


def check_disk(path=None, min_free_gb=10):
    target = path or str(Path.home())

    try:
        usage = shutil.disk_usage(target)
        free_gb = usage.free / (1024 ** 3)

        if free_gb >= min_free_gb:
            status = InspectionStatus.PASS
            error_type = ErrorType.NONE
        else:
            status = InspectionStatus.FAIL
            error_type = ErrorType.THRESHOLD

        message = f"剩余空间 {free_gb:.2f} GB，要求至少 {min_free_gb} GB"

    except OSError as exc:
        status = InspectionStatus.FAIL
        error_type = ErrorType.UNEXPECTED
        message = f"磁盘检查失败：{exc}"

    return InspectionResult(
        item="disk",
        target=target,
        status=status,
        message=message,
        error_type=error_type,
    )


def check_port(host, port, timeout=3):
    target = f"{host}:{port}"

    try:
        with socket.create_connection((host, port), timeout=timeout):
            status = InspectionStatus.PASS
            error_type = ErrorType.NONE
            message = f"{target} 可以建立TCP连接"

    except socket.timeout as exc:
        status = InspectionStatus.FAIL
        error_type = ErrorType.TIMEOUT
        message = f"{target} 连接失败：{exc}"

    except OSError as exc:
        status = InspectionStatus.FAIL
        error_type = ErrorType.CONNECTION
        message = f"{target} 连接失败：{exc}"

    return InspectionResult(
        item="tcp_port",
        target=target,
        status=status,
        message=message,
        error_type=error_type,
    )


def check_http(url, timeout=5):
    try:
        with request.urlopen(url, timeout=timeout) as response:
            status_code = response.getcode()

            if status_code == 200:
                status = InspectionStatus.PASS
                error_type = ErrorType.NONE
            else:
                status = InspectionStatus.FAIL
                error_type = ErrorType.HTTP_STATUS

            message = f"{url} 返回HTTP {status_code}"

    except error.HTTPError as exc:
        status = InspectionStatus.FAIL
        error_type = ErrorType.HTTP_STATUS
        message = f"{url} 返回HTTP {exc.code}"

    except error.URLError as exc:
        reason = exc.reason
        status = InspectionStatus.FAIL

        if isinstance(reason, TimeoutError):
            error_type = ErrorType.TIMEOUT
        else:
            error_type = ErrorType.CONNECTION

        message = f"{url} 请求失败：{reason}"

    except (TimeoutError, OSError) as exc:
        status = InspectionStatus.FAIL

        if isinstance(exc, TimeoutError):
            error_type = ErrorType.TIMEOUT
        else:
            error_type = ErrorType.CONNECTION

        message = f"{url} 请求失败：{exc}"

    return InspectionResult(
        item="http_health",
        target=url,
        status=status,
        message=message,
        error_type=error_type,
    )

def check_mysql(
    host,
    port=3306,
    user="root",
    password="",
    database=None,
    timeout=5,
):
    """连接 MySQL 并执行 SELECT 1，验证数据库是否可用。"""

    started_at = time.perf_counter()
    target = f"{host}:{port}"
    connection = None

    try:
        connect_options = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "connect_timeout": timeout,
            "read_timeout": timeout,
            "write_timeout": timeout,
            "charset": "utf8mb4",
        }

        if database:
            connect_options["database"] = database

        connection = pymysql.connect(**connect_options)

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()

        if row == (1,):
            return InspectionResult(
                item="mysql_health",
                target=target,
                status=InspectionStatus.PASS,
                message=f"{target} MySQL连接和查询正常",
                duration_ms=round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
            )

        return InspectionResult(
            item="mysql_health",
            target=target,
            status=InspectionStatus.FAIL,
            message=f"{target} MySQL返回异常结果：{row!r}",
            duration_ms=round(
                (time.perf_counter() - started_at) * 1000,
                2,
            ),
            error_type=ErrorType.UNEXPECTED,
        )

    except pymysql.err.OperationalError as exc:
        message = str(exc)

        if "timed out" in message.lower():
            error_type = ErrorType.TIMEOUT
        else:
            error_type = ErrorType.CONNECTION

        return InspectionResult(
            item="mysql_health",
            target=target,
            status=InspectionStatus.FAIL,
            message=f"{target} MySQL连接或查询失败：{exc}",
            duration_ms=round(
                (time.perf_counter() - started_at) * 1000,
                2,
            ),
            error_type=error_type,
        )

    except Exception as exc:
        return InspectionResult(
            item="mysql_health",
            target=target,
            status=InspectionStatus.FAIL,
            message=f"{target} MySQL检查异常：{exc}",
            duration_ms=round(
                (time.perf_counter() - started_at) * 1000,
                2,
            ),
            error_type=ErrorType.UNEXPECTED,
        )

    finally:
        if connection is not None:
            connection.close()