from urllib import error, request
from datetime import datetime
from pathlib import Path
import shutil
import socket
import sqlite3
import csv
import json


def check_disk(path=None, min_free_gb=10):
    """检查磁盘剩余空间是否达到要求。"""
    target = Path(path or Path.home().anchor)
    usage = shutil.disk_usage(target)

    free_gb = usage.free / (1024 ** 3)
    status = "PASS" if free_gb >= min_free_gb else "FAIL"

    return {
        "item": "disk_free",
        "target": str(target),
        "status": status,
        "message": (
            f"剩余空间 {free_gb:.2f} GB，"
            f"要求至少 {min_free_gb} GB"
        ),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def check_port(host, port, timeout=3):
    """检查目标主机的TCP端口是否可以建立连接。"""
    target = f"{host}:{port}"

    try:
        with socket.create_connection(
            (host, port),
            timeout=timeout,
        ):
            status = "PASS"
            message = f"{target} 可以建立TCP连接"
    except OSError as error:
        status = "FAIL"
        message = f"{target} 连接失败：{error}"

    return {
        "item": "tcp_port",
        "target": target,
        "status": status,
        "message": message,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }

def check_http(url, timeout=5):
    """检查目标URL是否能够返回正常HTTP响应。"""
    try:
        with request.urlopen(url, timeout=timeout) as response:
            status_code = response.getcode()

        if 200 <= status_code < 400:
            status = "PASS"
            message = f"{url} 返回HTTP {status_code}"
        else:
            status = "FAIL"
            message = f"{url} 返回异常HTTP {status_code}"

    except error.HTTPError as http_error:
        status = "FAIL"
        message = f"{url} 返回HTTP {http_error.code}"

    except (error.URLError, TimeoutError, OSError) as request_error:
        status = "FAIL"
        message = f"{url} 请求失败：{request_error}"

    return {
        "item": "http_health",
        "target": url,
        "status": status,
        "message": message,
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }

def save_results(results, db_path="data/inspections.db"):
    """创建数据库表，并批量保存巡检结果。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inspection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                checked_at TEXT NOT NULL
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO inspection_results (
                item,
                target,
                status,
                message,
                checked_at
            )
            VALUES (
                :item,
                :target,
                :status,
                :message,
                :checked_at
            )
            """,
            results,
        )

        connection.commit()
    finally:
        connection.close()

def get_recent_results(limit=4, db_path="data/inspections.db"):
    """按照记录编号倒序查询最近的巡检结果。"""
    connection = sqlite3.connect(db_path)

    try:
        rows = connection.execute(
            """
            SELECT
                item,
                target,
                status,
                message,
                checked_at
            FROM inspection_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return rows
    finally:
        connection.close()

def export_results_csv(results, output_dir="reports"):
    """将本次巡检结果导出为CSV报告。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_dir) / f"inspection_{timestamp}.csv"

    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "item",
                "target",
                "status",
                "message",
                "checked_at",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    return report_path

def print_result(result):
    """在终端中打印一条巡检结果。"""
    print(
        f"[{result['status']}] "
        f"{result['item']}: {result['message']}"
    )

def load_config(config_path="config.json"):
    """从JSON文件读取巡检配置。"""
    with Path(config_path).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def run_checks(config):
    """根据配置依次执行所有巡检任务。"""
    disk_config = config["disk"]
    results = [
        check_disk(
            path=disk_config["path"],
            min_free_gb=disk_config["min_free_gb"],
        )
    ]

    for port_config in config["ports"]:
        results.append(
            check_port(
                host=port_config["host"],
                port=port_config["port"],
                timeout=port_config.get("timeout", 3),
            )
        )

    for http_config in config["http_checks"]:
        results.append(
            check_http(
                url=http_config["url"],
                timeout=http_config.get("timeout", 5),
            )
        )

    return results

def summarize_results(results):
    """统计巡检结果数量。"""
    passed_count = sum(
        1 for result in results
        if result["status"] == "PASS"
    )
    failed_count = sum(
        1 for result in results
        if result["status"] == "FAIL"
    )

    return {
        "total": len(results),
        "passed": passed_count,
        "failed": failed_count,
    }

def main():
    config = load_config()
    results = run_checks(config)

    print("本次巡检结果：")
    for result in results:
        print_result(result)

    summary = summarize_results(results)
    print(
        f"\n巡检汇总：共 {summary['total']} 项，"
        f"PASS {summary['passed']} 项，"
        f"FAIL {summary['failed']} 项"
    )

    save_results(results)

    recent_results = get_recent_results(limit=4)
    print("\n数据库中最近4条记录：")
    for row in recent_results:
        item, target, status, message, checked_at = row
        print(f"{checked_at} [{status}] {item}: {message}")

    report_path = export_results_csv(results)
    print(f"\nCSV报告已保存到：{report_path}")

    return 1 if summary["failed"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())