from __future__ import annotations

import asyncio
import gc
import json
import shutil
import sqlite3
import tempfile
import types
import unittest
from pathlib import Path
from queue import Queue
from unittest.mock import AsyncMock, patch

import requests

import myUtils.login as login_module


class FakeBiliClient:
    """模拟 biliup 的 B 站二维码登录客户端，避免测试依赖外部网络。"""

    def __init__(self, *_args, **_kwargs) -> None:
        self._BiliBili__session = type("SessionHolder", (), {"cookies": requests.cookies.RequestsCookieJar()})()
        self.persistence_path = ""
        self.cookies = None
        self.access_token = None
        self.refresh_token = None

    def get_qrcode(self) -> dict:
        return {
            "code": 0,
            "data": {
                "url": "https://example.com/bilibili-login-qrcode",
                "auth_code": "mock-auth-code",
            },
        }

    async def login_by_qrcode(self, _value: dict) -> dict:
        return {
            "code": 0,
            "data": {
                "cookie_info": {
                    "cookies": [
                        {"name": "SESSDATA", "value": "sess"},
                        {"name": "bili_jct", "value": "csrf"},
                    ]
                },
                "token_info": {
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                },
            },
        }

    def store(self) -> None:
        Path(self.persistence_path).write_text(
            json.dumps(
                {
                    **(self.cookies or {}),
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                }
            ),
            encoding="utf-8",
        )


class BilibiliWebLoginTests(unittest.TestCase):
    """验证历史 Web B站登录流程可以生成二维码并落盘账号文件。"""

    def test_bilibili_cookie_gen_puts_qrcode_and_persists_account(self) -> None:
        temp_dir = tempfile.mkdtemp()
        try:
            base_dir = Path(temp_dir)
            (base_dir / "cookiesFile").mkdir(parents=True, exist_ok=True)
            (base_dir / "db").mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(base_dir / "db" / "database.db") as conn:
                conn.execute(
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

            status_queue = Queue()
            fake_module = types.ModuleType("biliup.plugins.bili_webup")
            fake_module.BiliBili = FakeBiliClient
            fake_module.Data = lambda: object()

            with patch.object(login_module, "BASE_DIR", base_dir), patch(
                "myUtils.login.check_cookie",
                new=AsyncMock(return_value=True),
            ), patch.dict(
                "sys.modules",
                {"biliup.plugins.bili_webup": fake_module},
            ):
                account_file = asyncio.run(login_module.bilibili_cookie_gen("creator", status_queue))

            self.assertIsNotNone(account_file)
            self.assertTrue(Path(account_file).exists())

            first_message = status_queue.get_nowait()
            second_message = status_queue.get_nowait()
            self.assertTrue(first_message.startswith("data:image/png;base64,"))
            self.assertEqual(second_message, "200")

            with sqlite3.connect(base_dir / "db" / "database.db") as conn:
                row = conn.execute("SELECT type, filePath, userName, status FROM user_info").fetchone()

            self.assertEqual(row[0], 5)
            self.assertEqual(row[2], "creator")
            self.assertEqual(row[3], 1)
            saved_payload = json.loads(Path(account_file).read_text(encoding="utf-8"))
            self.assertIn("cookie_info", saved_payload)
            self.assertIn("sso", saved_payload)
            self.assertIn("token_info", saved_payload)
            self.assertEqual(saved_payload["platform"], "Android")
            self.assertIn("expires_in", saved_payload["token_info"])
            self.assertIn("mid", saved_payload["token_info"])
        finally:
            gc.collect()
            for _ in range(5):
                try:
                    shutil.rmtree(temp_dir)
                    break
                except PermissionError:
                    import time
                    time.sleep(0.1)
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
