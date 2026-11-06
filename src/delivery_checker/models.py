from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum


class InspectionStatus(str, Enum):
    """巡检结果状态。"""

    PASS = "PASS"
    FAIL = "FAIL"


class ErrorType(str, Enum):
    """巡检失败或程序异常的类型。"""

    NONE = ""
    THRESHOLD = "threshold"
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    HTTP_STATUS = "http_status"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    UNEXPECTED = "unexpected"


def current_timestamp() -> str:
    """返回带本地时区信息的检查时间。"""

    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class InspectionResult:
    """一次巡检产生的统一结果。"""

    item: str
    target: str
    status: InspectionStatus
    message: str
    checked_at: str = field(default_factory=current_timestamp)
    duration_ms: float = 0.0
    attempts: int = 1
    error_type: ErrorType = ErrorType.NONE

    def to_dict(self) -> dict:
        """转换为字典，方便后续写入 SQLite 和 CSV。"""

        data = asdict(self)
        data["status"] = self.status.value
        data["error_type"] = self.error_type.value
        return data