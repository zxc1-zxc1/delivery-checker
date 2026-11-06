import unittest
from unittest.mock import patch

from delivery_checker.cli import main
from delivery_checker.config import ConfigError


class MainTest(unittest.TestCase):

    @patch(
        "delivery_checker.cli.load_config",
        side_effect=ConfigError("模拟配置错误"),
    )
    def test_config_error_returns_2(self, mocked_load_config):
        self.assertEqual(main(), 2)
        mocked_load_config.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()