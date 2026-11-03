import unittest
from unittest.mock import Mock, patch

from delivery_checker.models import (
    ErrorType,
    InspectionResult,
    InspectionStatus,
)
from delivery_checker.runner import run_with_retry


def make_result(status, error_type):
    return InspectionResult(
        item="test",
        target="local-test",
        status=status,
        message="模拟检查结果",
        error_type=error_type,
    )


class RetryTest(unittest.TestCase):

    def test_timeout_is_retried(self):
        outcomes = iter(
            [
                make_result(
                    InspectionStatus.FAIL,
                    ErrorType.TIMEOUT,
                ),
                make_result(
                    InspectionStatus.PASS,
                    ErrorType.NONE,
                ),
            ]
        )

        def fake_check():
            return next(outcomes)

        with patch("delivery_checker.runner.time.sleep") as mocked_sleep:
            result = run_with_retry(
                fake_check,
                max_attempts=2,
                retry_delay=0.1,
            )

        self.assertEqual(result.status, InspectionStatus.PASS)
        self.assertEqual(result.attempts, 2)
        self.assertGreaterEqual(result.duration_ms, 0.0)
        mocked_sleep.assert_called_once_with(0.1)

    def test_threshold_error_is_not_retried(self):
        mocked_check = Mock(
            return_value=make_result(
                InspectionStatus.FAIL,
                ErrorType.THRESHOLD,
            )
        )

        result = run_with_retry(
            mocked_check,
            max_attempts=3,
            retry_delay=0.1,
        )

        self.assertEqual(result.attempts, 1)
        mocked_check.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()