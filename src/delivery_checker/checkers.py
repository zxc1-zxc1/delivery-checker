import shutil
import socket
from pathlib import Path
from urllib import error, request

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