import json


def load_config(config_path="config.json") -> dict:
    """从 JSON 文件读取巡检配置。"""

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)