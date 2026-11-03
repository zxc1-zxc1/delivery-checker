import json
from urllib.parse import urlparse


class ConfigError(ValueError):
    """配置文件内容或格式错误。"""


def _validate_timeout(value, location):
    """校验超时时间必须是大于 0 的数字。"""

    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
    ):
        raise ConfigError(f"{location} 必须是大于 0 的数字")


def validate_config(config) -> dict:
    """校验巡检配置，校验通过后返回原配置。"""

    if not isinstance(config, dict):
        raise ConfigError("配置顶层必须是 JSON 对象")

    disk = config.get("disk", {})
    if not isinstance(disk, dict):
        raise ConfigError("disk 必须是 JSON 对象")

    disk_path = disk.get("path")
    if disk_path is not None:
        if not isinstance(disk_path, str) or not disk_path.strip():
            raise ConfigError("disk.path 必须是非空字符串")

    min_free_gb = disk.get("min_free_gb", 10)
    if (
        isinstance(min_free_gb, bool)
        or not isinstance(min_free_gb, (int, float))
        or min_free_gb < 0
    ):
        raise ConfigError("disk.min_free_gb 必须是大于或等于 0 的数字")

    ports = config.get("ports")
    if not isinstance(ports, list):
        raise ConfigError("ports 必须是数组")

    for index, item in enumerate(ports):
        location = f"ports[{index}]"

        if not isinstance(item, dict):
            raise ConfigError(f"{location} 必须是 JSON 对象")

        host = item.get("host")
        if not isinstance(host, str) or not host.strip():
            raise ConfigError(f"{location}.host 必须是非空字符串")

        port = item.get("port")
        if (
            isinstance(port, bool)
            or not isinstance(port, int)
            or not 1 <= port <= 65535
        ):
            raise ConfigError(
                f"{location}.port 必须是 1 到 65535 的整数"
            )

        _validate_timeout(item.get("timeout", 3), f"{location}.timeout")

    http_checks = config.get("http_checks")
    if not isinstance(http_checks, list):
        raise ConfigError("http_checks 必须是数组")

    for index, item in enumerate(http_checks):
        location = f"http_checks[{index}]"

        if not isinstance(item, dict):
            raise ConfigError(f"{location} 必须是 JSON 对象")

        url = item.get("url")
        if not isinstance(url, str):
            raise ConfigError(f"{location}.url 必须是字符串")

        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ConfigError(
                f"{location}.url 必须是有效的 http:// 或 https:// 地址"
            )

        _validate_timeout(item.get("timeout", 5), f"{location}.timeout")

    return config


def load_config(config_path="config.json") -> dict:
    """读取 JSON 配置，并在返回前完成校验。"""

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

    except FileNotFoundError as exc:
        raise ConfigError(f"配置文件不存在：{config_path}") from exc

    except json.JSONDecodeError as exc:
        raise ConfigError(
            f"JSON 格式错误：第 {exc.lineno} 行，第 {exc.colno} 列"
        ) from exc

    except OSError as exc:
        raise ConfigError(f"无法读取配置文件：{exc}") from exc

    return validate_config(config)