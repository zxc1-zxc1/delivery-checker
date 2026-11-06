
# from urllib import error, request
from datetime import datetime

from pathlib import Path
# import shutil
# import socket
import sqlite3
import csv
import json
from .config import ConfigError, load_config
from .logging_config import setup_logging
from .reporting import export_results_csv
from .runner import run_checks
from .storage import get_recent_results, save_results
import logging
# from delivery_checker.logging_config import setup_logging
logger = logging.getLogger("delivery_checker")

# def check_disk(path=None, min_free_gb=10):
#     target = path or str(Path.home())

#     try:
#         usage = shutil.disk_usage(target)
#         free_gb = usage.free / (1024 ** 3)

#         if free_gb >= min_free_gb:
#             status = InspectionStatus.PASS
#             error_type = ErrorType.NONE
#         else:
#             status = InspectionStatus.FAIL
#             error_type = ErrorType.THRESHOLD

#         message = f"剩余空间 {free_gb:.2f} GB，要求至少 {min_free_gb} GB"

#     except OSError as exc:
#         status = InspectionStatus.FAIL
#         error_type = ErrorType.UNEXPECTED
#         message = f"磁盘检查失败：{exc}"

#     return InspectionResult(
#         item="disk",
#         target=target,
#         status=status,
#         message=message,
#         error_type=error_type,
#     )


# def check_port(host, port, timeout=3):
#     target = f"{host}:{port}"

#     try:
#         with socket.create_connection((host, port), timeout=timeout):
#             status = InspectionStatus.PASS
#             error_type = ErrorType.NONE
#             message = f"{target} 可以建立TCP连接"

#     except socket.timeout as exc:
#         status = InspectionStatus.FAIL
#         error_type = ErrorType.TIMEOUT
#         message = f"{target} 连接失败：{exc}"

#     except OSError as exc:
#         status = InspectionStatus.FAIL
#         error_type = ErrorType.CONNECTION
#         message = f"{target} 连接失败：{exc}"

#     return InspectionResult(
#         item="tcp_port",
#         target=target,
#         status=status,
#         message=message,
#         error_type=error_type,
#     )

# def check_http(url, timeout=5):
#     try:
#         with request.urlopen(url, timeout=timeout) as response:
#             status_code = response.getcode()

#             if status_code == 200:
#                 status = InspectionStatus.PASS
#                 error_type = ErrorType.NONE
#             else:
#                 status = InspectionStatus.FAIL
#                 error_type = ErrorType.HTTP_STATUS

#             message = f"{url} 返回HTTP {status_code}"

#     except error.HTTPError as exc:
#         status = InspectionStatus.FAIL
#         error_type = ErrorType.HTTP_STATUS
#         message = f"{url} 返回HTTP {exc.code}"

#     except error.URLError as exc:
#         reason = exc.reason
#         status = InspectionStatus.FAIL

#         if isinstance(reason, TimeoutError):
#             error_type = ErrorType.TIMEOUT
#         else:
#             error_type = ErrorType.CONNECTION

#         message = f"{url} 请求失败：{reason}"

#     except (TimeoutError, OSError) as exc:
#         status = InspectionStatus.FAIL

#         if isinstance(exc, TimeoutError):
#             error_type = ErrorType.TIMEOUT
#         else:
#             error_type = ErrorType.CONNECTION

#         message = f"{url} 请求失败：{exc}"

#     return InspectionResult(
#         item="http_health",
#         target=url,
#         status=status,
#         message=message,
#         error_type=error_type,
#     )

# def save_results(results, db_path="data/inspections.db"):
#     """创建数据库表，并批量保存巡检结果。"""
#     db_path = Path(db_path)
#     db_path.parent.mkdir(parents=True, exist_ok=True)

#     connection = sqlite3.connect(db_path)

#     try:
#         connection.execute(
#             """
#             CREATE TABLE IF NOT EXISTS inspection_results (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 item TEXT NOT NULL,
#                 target TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 message TEXT NOT NULL,
#                 checked_at TEXT NOT NULL
#             )
#             """
#         )

#         connection.executemany(
#             """
#             INSERT INTO inspection_results (
#                 item,
#                 target,
#                 status,
#                 message,
#                 checked_at
#             )
#             VALUES (
#                 :item,
#                 :target,
#                 :status,
#                 :message,
#                 :checked_at
#             )
#             """,
#             results,
#         )

#         connection.commit()
#     finally:
#         connection.close()

# def get_recent_results(limit=4, db_path="data/inspections.db"):
#     """按照记录编号倒序查询最近的巡检结果。"""
#     connection = sqlite3.connect(db_path)

#     try:
#         rows = connection.execute(
#             """
#             SELECT
#                 item,
#                 target,
#                 status,
#                 message,
#                 checked_at
#             FROM inspection_results
#             ORDER BY id DESC
#             LIMIT ?
#             """,
#             (limit,),
#         ).fetchall()

#         return rows
#     finally:
#         connection.close()

# def export_results_csv(results, output_dir="reports"):
    # """将本次巡检结果导出为CSV报告。"""
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # report_path = Path(output_dir) / f"inspection_{timestamp}.csv"

    # report_path.parent.mkdir(parents=True, exist_ok=True)

    # with report_path.open(
    #     "w",
    #     newline="",
    #     encoding="utf-8-sig",
    # ) as file:
    #     writer = csv.DictWriter(
    #         file,
    #         fieldnames=[
    #             "item",
    #             "target",
    #             "status",
    #             "message",
    #             "checked_at",
    #         ],
    #         extrasaction="ignore",
    #     )
    #     writer.writeheader()
    #     writer.writerows(results)

    # return report_path

def print_result(result):
    """在终端中打印一条巡检结果。"""
    print(
        f"[{result['status']}] "
        f"{result['item']}: {result['message']}"
    )

# def load_config(config_path="config.json"):
#     """从JSON文件读取巡检配置。"""
#     with Path(config_path).open(
#         "r",
#         encoding="utf-8",
#     ) as file:
#         return json.load(file)


# def run_checks(config):
#     """根据配置依次执行所有巡检任务。"""
#     results = []

#     disk_config = config.get("disk", {})
#     disk_result = check_disk(
#         path=disk_config.get("path"),
#         min_free_gb=disk_config.get("min_free_gb", 10),
#     )
#     results.append(disk_result.to_dict())

#     for port_config in config["ports"]:
#         port_result = check_port(
#             host=port_config["host"],
#             port=port_config["port"],
#             timeout=port_config.get("timeout", 3),
#         )
#         results.append(port_result.to_dict())

#     for http_config in config["http_checks"]:
#         http_result = check_http(
#             url=http_config["url"],
#             timeout=http_config.get("timeout", 5),
#         )
#         results.append(http_result.to_dict())

#     return results

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
    logger.info("event=program_started")
    try:
        config = load_config()
    except ConfigError as exc:
        print(f"配置错误：{exc}")
        logger.error("event=config_error message=%s", exc)
        return 2

    logger.info("event=config_loaded")

    results = run_checks(config)
    logger.info("event=checks_completed count=%d", len(results))

    print("本次巡检结果：")
    for result in results:
        print_result(result)
        logger.info(
            "event=check_result item=%s target=%s status=%s "
            "error_type=%s attempts=%d duration_ms=%.2f",
            result["item"],
            result["target"],
            result["status"],
            result.get("error_type", ""),
            result.get("attempts", 1),
            result.get("duration_ms", 0.0),
        )

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

def entry_point():
    """供安装后的 delivery-checker 命令调用。"""

    setup_logging()
    return main()


if __name__ == "__main__":
    raise SystemExit(entry_point())