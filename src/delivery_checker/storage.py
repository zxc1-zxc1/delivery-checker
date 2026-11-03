import sqlite3
from pathlib import Path


def save_results(results, db_path="data/inspections.db"):
    """将本次巡检结果追加保存到 SQLite。"""

    database_path = Path(db_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inspection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                checked_at TEXT NOT NULL
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO inspection_results (
                item, target, status, message, checked_at
            )
            VALUES (
                :item, :target, :status, :message, :checked_at
            )
            """,
            results,
        )
        connection.commit()

    finally:
        connection.close()


def get_recent_results(limit=4, db_path="data/inspections.db"):
    """按倒序查询最近的巡检记录。"""

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.execute(
            """
            SELECT item, target, status, message, checked_at
            FROM inspection_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()

    finally:
        connection.close()