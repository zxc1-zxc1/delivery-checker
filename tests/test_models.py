import unittest

from delivery_checker.models import (
    ErrorType,
    InspectionResult,
    InspectionStatus,
)


class InspectionResultTest(unittest.TestCase):

    def test_default_values(self):
        result = InspectionResult(
            item="tcp_port",
            target="127.0.0.1:3306",
            status=InspectionStatus.PASS,
            message="连接成功",
        )

        self.assertEqual(result.duration_ms, 0.0)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(result.error_type, ErrorType.NONE)
        self.assertTrue(result.checked_at)

    def test_to_dict(self):
        result = InspectionResult(
            item="disk",
            target="D:/",
            status=InspectionStatus.FAIL,
            message="剩余空间不足",
            duration_ms=12.5,
            attempts=2,
            error_type=ErrorType.THRESHOLD,
        )

        data = result.to_dict()

        self.assertEqual(data["item"], "disk")
        self.assertEqual(data["status"], "FAIL")
        self.assertEqual(data["duration_ms"], 12.5)
        self.assertEqual(data["attempts"], 2)
        self.assertEqual(data["error_type"], "threshold")


if __name__ == "__main__":
    unittest.main()