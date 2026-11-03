import csv
from datetime import datetime
from pathlib import Path


def export_results_csv(results, output_dir="reports"):
    """将本次巡检结果导出为 CSV 报告。"""

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
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(results)

    return report_path