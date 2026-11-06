import unittest

from delivery_checker.config import ConfigError, validate_config


def make_valid_config():
    return {
        "disk": {
            "path": "D:/",
            "min_free_gb": 10,
        },
        "ports": [
            {
                "host": "127.0.0.1",
                "port": 443,
                "timeout": 3,
            }
        ],
        "http_checks": [
            {
                "url": "https://www.example.com",
                "timeout": 5,
            }
        ],
    }


class ConfigValidationTest(unittest.TestCase):

    def test_valid_config(self):
        config = make_valid_config()
        self.assertEqual(validate_config(config), config)

    def test_invalid_port(self):
        config = make_valid_config()
        config["ports"][0]["port"] = 70000

        with self.assertRaises(ConfigError) as context:
            validate_config(config)

        self.assertIn("ports[0].port", str(context.exception))

    def test_invalid_timeout(self):
        config = make_valid_config()
        config["ports"][0]["timeout"] = 0

        with self.assertRaises(ConfigError) as context:
            validate_config(config)

        self.assertIn("ports[0].timeout", str(context.exception))

    def test_invalid_http_url(self):
        config = make_valid_config()
        config["http_checks"][0]["url"] = "ftp://example.com"

        with self.assertRaises(ConfigError) as context:
            validate_config(config)

        self.assertIn("http_checks[0].url", str(context.exception))

    def test_invalid_max_attempts(self):
        config = make_valid_config()
        config["ports"][0]["max_attempts"] = 0

        with self.assertRaises(ConfigError) as context:
            validate_config(config)

        self.assertIn("ports[0].max_attempts", str(context.exception))

    def test_mysql_password_must_use_environment_variable_name(self):
        config = {
            "mysql_checks": [
                {
                    "host": "127.0.0.1",
                    "user": "inspector",
                    "password_env": "",
                }
            ]
        }

        with self.assertRaises(ConfigError):
            validate_config(config)

if __name__ == "__main__":
    unittest.main()
