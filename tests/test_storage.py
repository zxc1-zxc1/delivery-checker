import sqlite3
import tempfile
import unittest
from pathlib import Path

from delivery_checker.storage import get_recent_results, save_results


class StorageTest(unittest.TestCase):

    def test_old_database_is_upgraded_and_v2_fields_are_saved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "inspections.db"
            connection = sqlite3.connect(db_path)

            connection.execute(
                """
                CREATE TABLE inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    checked_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO inspections (
                    item, target, status, message, checked_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "disk",
                    ".",
                    "PASS",
                    "旧版本记录",
                    "2026-01-01T00:00:00+08:00",
                ),
            )
            connection.commit()
            connection.close()

            new_result = {
                "item": "tcp_port",
                "target": "127.0.0.1:443",
                "status": "FAIL",
                "message": "模拟连接失败",
                "checked_at": "2026-01-01T00:01:00+08:00",
                "duration_ms": 123.45,
                "attempts": 2,
                "error_type": "connection",
            }
            save_results([new_result], db_path=db_path)

            connection = sqlite3.connect(db_path)
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(inspections)"
                )
            }
            saved_fields = connection.execute(
                """
                SELECT duration_ms, attempts, error_type
                FROM inspections
                WHERE item = 'tcp_port'
                """
            ).fetchone()
            old_defaults = connection.execute(
                """
                SELECT duration_ms, attempts, error_type
                FROM inspections
                WHERE item = 'disk'
                """
            ).fetchone()
            connection.close()

            self.assertTrue(
                {"duration_ms", "attempts", "error_type"}.issubset(columns)
            )
            self.assertEqual(saved_fields, (123.45, 2, "connection"))
            self.assertEqual(old_defaults, (0.0, 1, ""))

            recent_results = get_recent_results(
                limit=10,
                db_path=db_path,
            )
            self.assertEqual(len(recent_results), 2)
            self.assertEqual(len(recent_results[0]), 5)


if __name__ == "__main__":
    unittest.main()