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


if __name__ == "__main__":
    unittest.main()
    