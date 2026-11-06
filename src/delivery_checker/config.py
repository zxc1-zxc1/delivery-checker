import json
from urllib.parse import urlparse


class ConfigError(ValueError):
    """配置错误。"""


def load_config(config_path="config.json") -> dict:
    """读取并校验 JSON 配置。"""

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"配置文件不存在：{config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"配置文件不是有效的 JSON：第 {exc.lineno} 行，第 {exc.colno} 列"
        ) from exc
    except OSError as exc:
        raise ConfigError(f"读取配置文件失败：{exc}") from exc

    return validate_config(config)


def validate_config(config) -> dict:
    """校验配置结构和字段，校验成功后返回原配置。"""

    if not isinstance(config, dict):
        raise ConfigError("配置顶层必须是 JSON 对象")

    disk = config.get("disk", {})
    if not isinstance(disk, dict):
        raise ConfigError("disk 必须是对象")

    disk_path = disk.get("path")
    if disk_path is not None and not isinstance(disk_path, str):
        raise ConfigError("disk.path 必须是字符串或 null")

    min_free_gb = disk.get("min_free_gb", 10)
    if (
        isinstance(min_free_gb, bool)
        or not isinstance(min_free_gb, (int, float))
        or min_free_gb < 0
    ):
        raise ConfigError("disk.min_free_gb 必须是大于或等于 0 的数字")

    ports = config.get("ports", [])
    if not isinstance(ports, list):
        raise ConfigError("ports 必须是数组")

    for index, item in enumerate(ports):
        location = f"ports[{index}]"
        _validate_check_object(item, location)

        host = item.get("host")
        if not isinstance(host, str) or not host.strip():
            raise ConfigError(f"{location}.host 必须是非空字符串")

        _validate_port(item.get("port"), f"{location}.port")
        _validate_timeout(item, location)
        _validate_retry_options(item, location)

    http_checks = config.get("http_checks", [])
    if not isinstance(http_checks, list):
        raise ConfigError("http_checks 必须是数组")

    for index, item in enumerate(http_checks):
        location = f"http_checks[{index}]"
        _validate_check_object(item, location)

        url = item.get("url")
        if not isinstance(url, str):
            raise ConfigError(f"{location}.url 必须是字符串")

        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ConfigError(
                f"{location}.url 必须是有效的 HTTP 或 HTTPS 地址"
            )

        _validate_timeout(item, location)
        _validate_retry_options(item, location)

    mysql_checks = config.get("mysql_checks", [])
    if not isinstance(mysql_checks, list):
        raise ConfigError("mysql_checks 必须是数组")

    for index, item in enumerate(mysql_checks):
        location = f"mysql_checks[{index}]"
        _validate_check_object(item, location)

        host = item.get("host")
        if not isinstance(host, str) or not host.strip():
            raise ConfigError(f"{location}.host 必须是非空字符串")

        _validate_port(item.get("port", 3306), f"{location}.port")

        user = item.get("user")
        if not isinstance(user, str) or not user:
            raise ConfigError(f"{location}.user 必须是非空字符串")

        database = item.get("database")
        if database is not None and (
            not isinstance(database, str) or not database
        ):
            raise ConfigError(
                f"{location}.database 必须是非空字符串或 null"
            )

        password_env = item.get(
            "password_env",
            "DELIVERY_CHECKER_MYSQL_PASSWORD",
        )
        if not isinstance(password_env, str) or not password_env:
            raise ConfigError(
                f"{location}.password_env 必须是非空字符串"
            )

        _validate_timeout(item, location)
        _validate_retry_options(item, location)

    return config


def _validate_check_object(item, location):
    if not isinstance(item, dict):
        raise ConfigError(f"{location} 必须是对象")


def _validate_port(port, location):
    if (
        isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
    ):
        raise ConfigError(f"{location} 必须是 1 到 65535 之间的整数")


def _validate_timeout(item, location):
    timeout = item.get("timeout", 3)
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or timeout <= 0
    ):
        raise ConfigError(f"{location}.timeout 必须是大于 0 的数字")


def _validate_retry_options(item, location):
    max_attempts = item.get("max_attempts", 1)
    if (
        isinstance(max_attempts, bool)
        or not isinstance(max_attempts, int)
        or max_attempts < 1
    ):
        raise ConfigError(
            f"{location}.max_attempts 必须是大于或等于 1 的整数"
        )

    retry_delay = item.get("retry_delay", 0.2)
    if (
        isinstance(retry_delay, bool)
        or not isinstance(retry_delay, (int, float))
        or retry_delay < 0
    ):
        raise ConfigError(
            f"{location}.retry_delay 必须是大于或等于 0 的数字"
        )