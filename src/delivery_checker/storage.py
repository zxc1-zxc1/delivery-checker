import sqlite3
from pathlib import Path


def _ensure_schema(connection):
    """创建数据表，并为旧版本数据库补充新增字段。"""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            target TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            duration_ms REAL NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 1,
            error_type TEXT NOT NULL DEFAULT ''
        )
        """
    )

    existing_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(inspections)")
    }

    migrations = {
        "duration_ms": "REAL NOT NULL DEFAULT 0",
        "attempts": "INTEGER NOT NULL DEFAULT 1",
        "error_type": "TEXT NOT NULL DEFAULT ''",
    }

    for column, definition in migrations.items():
        if column not in existing_columns:
            connection.execute(
                f"ALTER TABLE inspections ADD COLUMN {column} {definition}"
            )


def save_results(results, db_path="data/inspections.db"):
    """批量保存巡检结果，并保留 V2 新增字段。"""

    database = Path(db_path)
    database.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database)

    try:
        _ensure_schema(connection)

        rows = [
            (
                result["item"],
                result["target"],
                result["status"],
                result["message"],
                result["checked_at"],
                result.get("duration_ms", 0.0),
                result.get("attempts", 1),
                result.get("error_type", ""),
            )
            for result in results
        ]

        connection.executemany(
            """
            INSERT INTO inspections (
                item,
                target,
                status,
                message,
                checked_at,
                duration_ms,
                attempts,
                error_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()

    finally:
        connection.close()


def get_recent_results(limit=4, db_path="data/inspections.db"):
    """按时间倒序查询最近记录，保持原有五列返回格式。"""

    database = Path(db_path)
    database.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database)

    try:
        _ensure_schema(connection)
        connection.commit()

        cursor = connection.execute(
            """
            SELECT item, target, status, message, checked_at
            FROM inspections
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()

    finally:
        connection.close()