import mysql.connector

from core.config import ConfigManager


class PollRepository:
    def _connect(self):
        cfg = ConfigManager.get_db_config()
        return mysql.connector.connect(
            **{**cfg, "autocommit": bool(cfg.get("autocommit", True))}
        )

    def fetch_all_polls(self) -> list:
        with self._connect() as mydb:
            cursor = mydb.cursor(dictionary=True)
            cursor.execute("SELECT * FROM polls")
            return cursor.fetchall()

    def fetch_poll_by_title(self, title: str) -> dict:
        with self._connect() as mydb:
            cursor = mydb.cursor(dictionary=True)
            cursor.execute("SELECT * FROM polls WHERE `title` = %s", (title,))
            return cursor.fetchall()[0]
