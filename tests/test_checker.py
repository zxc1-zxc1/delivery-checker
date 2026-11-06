import csv
import tempfile
import unittest
from pathlib import Path
from delivery_checker.cli import summarize_results

from delivery_checker.cli import(
    export_results_csv,
    get_recent_results,
    save_results,
    summarize_results,
)


class DeliveryCheckerTests(unittest.TestCase):

    def test_summarize_results(self):
        """测试正常和异常数量的统计。"""
        results = [
            {"status": "PASS"},
            {"status": "FAIL"},
            {"status": "PASS"},
        ]

        summary = summarize_results(results)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["passed"], 2)
        self.assertEqual(summary["failed"], 1)

    def test_database_save_and_query(self):
        """测试巡检结果能否保存并重新查询。"""
        results = [
            {
                "item": "disk_free",
                "target": "D:/",
                "status": "PASS",
                "message": "测试磁盘巡检",
                "checked_at": "2026-10-29T06:00:00",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            save_results(results, db_path=db_path)
            rows = get_recent_results(
                limit=4,
                db_path=db_path,
            )

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], "disk_free")
            self.assertEqual(rows[0][2], "PASS")

    def test_export_results_csv(self):
        """测试CSV报告是否生成，以及内容是否正确。"""
        results = [
            {
                "item": "http_health",
                "target": "https://example.com",
                "status": "PASS",
                "message": "返回HTTP 200",
                "checked_at": "2026-10-29T06:00:00",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = export_results_csv(
                results,
                output_dir=temp_dir,
            )

            self.assertTrue(report_path.exists())

            with report_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                rows = list(csv.DictReader(file))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["item"], "http_health")
            self.assertEqual(rows[0]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()