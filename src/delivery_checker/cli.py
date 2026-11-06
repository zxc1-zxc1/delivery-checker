

import logging

from .config import ConfigError, load_config
from .logging_config import setup_logging
from .reporting import export_results_csv
from .runner import run_checks
from .storage import get_recent_results, save_results

logger = logging.getLogger("delivery_checker")




































def print_result(result):
    """在终端中打印一条巡检结果。"""
    print(
        f"[{result['status']}] "
        f"{result['item']}: {result['message']}"
    )








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
