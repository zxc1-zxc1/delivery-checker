import unittest
from unittest.mock import MagicMock, patch

import pymysql

from delivery_checker.checkers import check_mysql
from delivery_checker.models import ErrorType, InspectionStatus


class MysqlCheckerTest(unittest.TestCase):

    @patch("delivery_checker.checkers.pymysql.connect")
    def test_mysql_connection_and_query_succeed(self, mocked_connect):
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (1,)
        connection.cursor.return_value.__enter__.return_value = cursor
        mocked_connect.return_value = connection

        result = check_mysql(
            host="127.0.0.1",
            user="tester",
            password="test-password",
            database="test_db",
        )

        self.assertEqual(result.status, InspectionStatus.PASS)
        self.assertEqual(result.error_type, ErrorType.NONE)
        self.assertEqual(result.item, "mysql_health")
        self.assertEqual(result.target, "127.0.0.1:3306")
        self.assertGreaterEqual(result.duration_ms, 0.0)

        cursor.execute.assert_called_once_with("SELECT 1")
        connection.close.assert_called_once_with()

        connect_options = mocked_connect.call_args.kwargs
        self.assertEqual(connect_options["host"], "127.0.0.1")
        self.assertEqual(connect_options["database"], "test_db")

    @patch("delivery_checker.checkers.pymysql.connect")
    def test_mysql_connection_failure(self, mocked_connect):
        mocked_connect.side_effect = pymysql.err.OperationalError(
            2003,
            "Can't connect to MySQL server",
        )

        result = check_mysql(
            host="127.0.0.1",
            user="tester",
            password="test-password",
        )

        self.assertEqual(result.status, InspectionStatus.FAIL)
        self.assertEqual(result.error_type, ErrorType.CONNECTION)
        self.assertNotIn("test-password", result.message)


if __name__ == "__main__":
    unittest.main()