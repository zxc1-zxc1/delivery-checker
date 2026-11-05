import csv
import tempfile
import unittest

from delivery_checker.reporting import export_results_csv


class ReportingTest(unittest.TestCase):

    def test_export_with_v2_fields(self):
        results = [
            {
                "item": "disk",
                "target": "D:/",
                "status": "PASS",
                "message": "剩余空间充足",
                "checked_at": "2026-11-03T21:00:00+08:00",
                "duration_ms": 12.5,
                "attempts": 1,
                "error_type": "",
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
                newline="",
                encoding="utf-8-sig",
            ) as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["item"], "disk")
        self.assertEqual(rows[0]["target"], "D:/")
        self.assertEqual(rows[0]["status"], "PASS")

    def test_csv_contains_v2_columns(self):
        results = [
            {
                "item": "tcp_port",
                "target": "127.0.0.1:443",
                "status": "FAIL",
                "message": "模拟连接失败",
                "checked_at": "2026-01-01T00:00:00+08:00",
                "duration_ms": 123.45,
                "attempts": 2,
                "error_type": "connection",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = export_results_csv(
                results,
                output_dir=temp_dir,
            )

            with open(
                output_path,
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as file:
                reader = csv.DictReader(file)
                rows = list(reader)

        self.assertEqual(
            reader.fieldnames,
            [
                "item",
                "target",
                "status",
                "message",
                "checked_at",
                "duration_ms",
                "attempts",
                "error_type",
            ],
        )
        self.assertEqual(rows[0]["duration_ms"], "123.45")
        self.assertEqual(rows[0]["attempts"], "2")
        self.assertEqual(rows[0]["error_type"], "connection")

if __name__ == "__main__":
    unittest.main()
