import asyncio
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import myUtils.login as legacy_login


class _MemoryQueue:
    """收集 SSE 推送内容，便于断言历史 Web 登录流程的输出顺序。"""

    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


class LegacyDouyinWebLoginTests(unittest.TestCase):
    """验证历史 Web 抖音登录对主线登录结果的适配行为。"""

    def _prepare_database(self, base_dir: Path) -> Path:
        db_dir = base_dir / "db"
        db_dir.mkdir()
        db_path = db_dir / "database.db"
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE user_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type INTEGER NOT NULL,
                    filePath TEXT NOT NULL,
                    userName TEXT NOT NULL,
                    status INTEGER DEFAULT 0
                )
                """
            )
            conn.commit()
        return db_path

    def test_douyin_cookie_gen_reports_qrcode_and_success_from_mainline_flow(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            base_dir = Path(tmp_dir)
            db_path = self._prepare_database(base_dir)
            queue = _MemoryQueue()

            async def fake_mainline(account_file, qrcode_callback=None, headless=True):
                self.assertTrue(str(account_file).endswith("fixed-uuid.json"))
                Path(account_file).parent.mkdir(exist_ok=True)
                Path(account_file).write_text("{}", encoding="utf-8")
                if qrcode_callback:
                    await qrcode_callback(
                        {
                            "image_data_url": "data:image/png;base64,abc",
                            "image_path": str(base_dir / "qrcode.png"),
                        }
                    )
                return {"success": True, "message": "ok"}

            with patch("myUtils.login.BASE_DIR", base_dir), patch(
                "myUtils.login.uuid.uuid1", return_value="fixed-uuid"
            ), patch(
                "myUtils.login.mainline_douyin_cookie_gen",
                new=AsyncMock(side_effect=fake_mainline),
            ):
                asyncio.run(legacy_login.douyin_cookie_gen("creator", queue))

            self.assertEqual(queue.items, ["data:image/png;base64,abc", "200"])
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    "SELECT type, filePath, userName, status FROM user_info"
                ).fetchall()
            self.assertEqual(rows, [(3, "fixed-uuid.json", "creator", 1)])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_douyin_cookie_gen_reports_failure_without_writing_user_record(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            base_dir = Path(tmp_dir)
            db_path = self._prepare_database(base_dir)
            queue = _MemoryQueue()

            async def fake_mainline(account_file, qrcode_callback=None, headless=True):
                if qrcode_callback:
                    await qrcode_callback(
                        {
                            "image_data_url": "data:image/png;base64,expired",
                            "image_path": str(base_dir / "qrcode.png"),
                        }
                    )
                return {"success": False, "message": "timeout"}

            with patch("myUtils.login.BASE_DIR", base_dir), patch(
                "myUtils.login.uuid.uuid1", return_value="fixed-uuid"
            ), patch(
                "myUtils.login.mainline_douyin_cookie_gen",
                new=AsyncMock(side_effect=fake_mainline),
            ):
                asyncio.run(legacy_login.douyin_cookie_gen("creator", queue))

            self.assertEqual(queue.items, ["data:image/png;base64,expired", "500"])
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute("SELECT COUNT(*) FROM user_info").fetchone()[0]
            self.assertEqual(rows, 0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
