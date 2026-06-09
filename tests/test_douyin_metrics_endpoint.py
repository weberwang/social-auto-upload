import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import sau_backend
from myUtils.douyin_metrics import DouyinAccountMetricsSnapshot


class DouyinMetricsEndpointTests(unittest.TestCase):
    """覆盖抖音运营数据接口的账号筛选和结果透传行为。"""

    def setUp(self):
        """为每个用例准备隔离数据库，避免账号数据互相污染。"""

        self.client = sau_backend.app.test_client()
        self.base_dir = Path(tempfile.mkdtemp())
        self._prepare_database()

    def tearDown(self):
        """清理临时目录，避免测试残留 Cookie 和数据库文件。"""

        shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_get_douyin_account_metrics_returns_snapshot_for_douyin_account(self):
        """抖音账号应能通过接口拿到当前运营概览。"""

        self._insert_account(account_id=1, platform_type=3, file_path="douyin_creator.json", user_name="抖音主号")
        expected_snapshot = DouyinAccountMetricsSnapshot(
            account_name="抖音主号",
            account_file="douyin_creator.json",
            current_url="https://creator.douyin.com/creator-micro/home",
            captured_at="2026-06-09T15:00:00",
            follower_count=12000,
            like_count=34000,
            following_count=78,
            work_count=56,
            total_view_count=91000,
            raw_metrics={"粉丝数": 12000, "获赞": 34000},
        )

        with patch("sau_backend.BASE_DIR", self.base_dir), patch(
            "sau_backend.fetch_douyin_account_metrics",
            new=AsyncMock(return_value=expected_snapshot),
        ) as mock_fetch:
            response = self.client.get("/getDouyinAccountMetrics?id=1")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["platform"], "douyin")
        self.assertEqual(payload["data"]["account_name"], "抖音主号")
        self.assertEqual(payload["data"]["captured_at"], "2026-06-09T15:00:00")
        self.assertEqual(payload["data"]["follower_count"], 12000)
        self.assertEqual(payload["data"]["like_count"], 34000)
        self.assertEqual(payload["data"]["work_count"], 56)
        mock_fetch.assert_awaited_once_with(
            self.base_dir / "cookiesFile" / "douyin_creator.json",
            "抖音主号",
        )

    def test_get_douyin_account_metrics_rejects_non_douyin_account(self):
        """非抖音账号不应误走抖音运营数据抓取链路。"""

        self._insert_account(account_id=2, platform_type=5, file_path="bilibili_creator.json", user_name="B站主号")

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.get("/getDouyinAccountMetrics?id=2")

        self.assertEqual(response.status_code, 400)
        self.assertIn("仅支持抖音账号", response.get_json()["msg"])

    def test_get_douyin_account_metrics_returns_not_found_for_missing_account(self):
        """账号不存在时应返回 404，而不是落成通用 500。"""

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.get("/getDouyinAccountMetrics?id=999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("账号不存在", response.get_json()["msg"])

    def _prepare_database(self):
        """创建接口测试所需的最小账号表结构。"""

        db_dir = self.base_dir / "db"
        cookie_dir = self.base_dir / "cookiesFile"
        db_dir.mkdir(parents=True, exist_ok=True)
        cookie_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_dir / "database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE user_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type INTEGER NOT NULL,
                    filePath TEXT NOT NULL,
                    userName TEXT NOT NULL,
                    status INTEGER DEFAULT 1
                )
                """
            )
            conn.commit()

    def _insert_account(self, account_id: int, platform_type: int, file_path: str, user_name: str):
        """写入单条账号记录，并同步生成占位 Cookie 文件路径。"""

        (self.base_dir / "cookiesFile" / file_path).write_text("{}", encoding="utf-8")
        with sqlite3.connect(self.base_dir / "db" / "database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_info (id, type, filePath, userName, status)
                VALUES (?, ?, ?, ?, 1)
                """,
                (account_id, platform_type, file_path, user_name),
            )
            conn.commit()


if __name__ == "__main__":
    unittest.main()
