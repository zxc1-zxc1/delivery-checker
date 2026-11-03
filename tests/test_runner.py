import threading
import unittest
from unittest.mock import Mock, patch

from delivery_checker.models import (
    ErrorType,
    InspectionResult,
    InspectionStatus,
)
from delivery_checker.runner import run_checks, run_with_retry


def make_result(
    status,
    error_type,
    item="test",
    target="local-test",
):
    return InspectionResult(
        item=item,
        target=target,
        status=status,
        message="模拟检查结果",
        error_type=error_type,
    )


class RunnerTest(unittest.TestCase):

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

    def test_network_checks_run_concurrently_and_keep_order(self):
        barrier = threading.Barrier(2)

        def fake_port_check(**kwargs):
            barrier.wait(timeout=2)
            return make_result(
                InspectionStatus.PASS,
                ErrorType.NONE,
                item="tcp_port",
                target="localhost:443",
            )

        def fake_http_check(**kwargs):
            barrier.wait(timeout=2)
            return make_result(
                InspectionStatus.PASS,
                ErrorType.NONE,
                item="http_health",
                target="https://example.com",
            )

        config = {
            "disk": {},
            "ports": [
                {
                    "host": "localhost",
                    "port": 443,
                }
            ],
            "http_checks": [
                {
                    "url": "https://example.com",
                }
            ],
        }

        with (
            patch("delivery_checker.runner.check_disk") as mocked_disk,
            patch(
                "delivery_checker.runner.check_port",
                side_effect=fake_port_check,
            ),
            patch(
                "delivery_checker.runner.check_http",
                side_effect=fake_http_check,
            ),
        ):
            mocked_disk.return_value = make_result(
                InspectionStatus.PASS,
                ErrorType.NONE,
                item="disk",
                target=".",
            )
            results = run_checks(config)

        self.assertEqual(
            [result["item"] for result in results],
            ["disk", "tcp_port", "http_health"],
        )
        self.assertEqual(
            [result["status"] for result in results],
            ["PASS", "PASS", "PASS"],
        )


if __name__ == "__main__":
    unittest.main()