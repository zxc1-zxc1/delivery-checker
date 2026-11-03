from .checkers import check_disk, check_http, check_port


def run_checks(config) -> list[dict]:
    """根据配置依次执行所有巡检任务。"""

    results = []

    disk_config = config.get("disk", {})
    disk_result = check_disk(
        path=disk_config.get("path"),
        min_free_gb=disk_config.get("min_free_gb", 10),
    )
    results.append(disk_result.to_dict())

    for port_config in config["ports"]:
        port_result = check_port(
            host=port_config["host"],
            port=port_config["port"],
            timeout=port_config.get("timeout", 3),
        )
        results.append(port_result.to_dict())

    for http_config in config["http_checks"]:
        http_result = check_http(
            url=http_config["url"],
            timeout=http_config.get("timeout", 5),
        )
        results.append(http_result.to_dict())

    return results