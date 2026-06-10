import asyncio
import shutil
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
sys.modules.setdefault("conf", conf_stub)

segno_stub = types.ModuleType("segno")
segno_stub.make = lambda *_args, **_kwargs: types.SimpleNamespace(save=lambda *a, **k: None)
sys.modules.setdefault("segno", segno_stub)

auth_stub = types.ModuleType("myUtils.auth")


async def _stub_check_cookie(*_args, **_kwargs):
    return True


auth_stub.check_cookie = _stub_check_cookie
sys.modules.setdefault("myUtils.auth", auth_stub)

base_social_media_stub = types.ModuleType("utils.base_social_media")


async def _stub_set_init_script(context):
    return context


base_social_media_stub.set_init_script = _stub_set_init_script
sys.modules.setdefault("utils.base_social_media", base_social_media_stub)

playwright_stub = types.ModuleType("playwright.async_api")
playwright_stub.async_playwright = lambda: None
playwright_stub.Error = Exception
sys.modules.setdefault("playwright.async_api", playwright_stub)

logger_stub = types.SimpleNamespace(
    info=lambda *_args, **_kwargs: None,
    success=lambda *_args, **_kwargs: None,
    warning=lambda *_args, **_kwargs: None,
    error=lambda *_args, **_kwargs: None,
    exception=lambda *_args, **_kwargs: None,
)
utils_log_stub = types.ModuleType("utils.log")
utils_log_stub.bilibili_logger = logger_stub
utils_log_stub.tencent_logger = logger_stub
utils_log_stub.kuaishou_logger = logger_stub
utils_log_stub.douyin_logger = logger_stub
utils_log_stub.xhs_logger = logger_stub
utils_log_stub.wechatmp_logger = logger_stub
sys.modules.setdefault("utils.log", utils_log_stub)

import myUtils.login as legacy_login


class _MemoryQueue:
    """收集 SSE 推送内容，便于断言历史 Web 微信公众号登录流程的输出顺序。"""

    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


class LegacyWechatOfficialAccountWebLoginTests(unittest.TestCase):
    """验证历史 Web 微信公众号登录会复用主线登录能力并正确回写状态。"""

    def _prepare_database(self, base_dir: Path) -> Path:
        """创建测试数据库，模拟历史 Web 账号表结构。"""

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

    def test_get_wechatmp_cookie_reports_qrcode_and_success_from_mainline_flow(self):
        """登录成功时应透传二维码、写入账号并推送成功终态。"""

        tmp_dir = tempfile.mkdtemp()
        try:
            base_dir = Path(tmp_dir)
            db_path = self._prepare_database(base_dir)
            queue = _MemoryQueue()

            async def fake_mainline(account_file, qrcode_callback=None, headless=True):
                self.assertFalse(headless)
                Path(account_file).parent.mkdir(exist_ok=True)
                Path(account_file).write_text("{}", encoding="utf-8")
                if qrcode_callback:
                    await qrcode_callback(
                        {
                            "image_data_url": "data:image/png;base64,wechatmp",
                            "image_path": str(base_dir / "qrcode.png"),
                        }
                    )
                return {"success": True, "message": "ok"}

            with patch("myUtils.login.BASE_DIR", base_dir), patch(
                "myUtils.login.uuid.uuid1", return_value="fixed-uuid"
            ), patch("builtins.print"), patch(
                "myUtils.login.mainline_wechatmp_cookie_gen",
                create=True,
                new=AsyncMock(side_effect=fake_mainline),
            ):
                asyncio.run(legacy_login.get_wechatmp_cookie("creator", queue))

            self.assertEqual(queue.items, ["data:image/png;base64,wechatmp", "200"])
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute("SELECT type, filePath, userName, status FROM user_info").fetchall()
            self.assertEqual(rows, [(6, "fixed-uuid.json", "creator", 1)])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_get_wechatmp_cookie_reports_failure_without_writing_user_record(self):
        """登录失败时应给前端明确失败终态，且不能写入账号记录。"""

        tmp_dir = tempfile.mkdtemp()
        try:
            base_dir = Path(tmp_dir)
            db_path = self._prepare_database(base_dir)
            queue = _MemoryQueue()

            async def fake_mainline(account_file, qrcode_callback=None, headless=True):
                self.assertFalse(headless)
                if qrcode_callback:
                    await qrcode_callback(
                        {
                            "image_data_url": "data:image/png;base64,wechatmp-expired",
                            "image_path": str(base_dir / "qrcode.png"),
                        }
                    )
                return {"success": False, "message": "等待微信公众号扫码登录超时"}

            with patch("myUtils.login.BASE_DIR", base_dir), patch(
                "myUtils.login.uuid.uuid1", return_value="fixed-uuid"
            ), patch("builtins.print"), patch(
                "myUtils.login.mainline_wechatmp_cookie_gen",
                create=True,
                new=AsyncMock(side_effect=fake_mainline),
            ):
                asyncio.run(legacy_login.get_wechatmp_cookie("creator", queue))

            self.assertEqual(
                queue.items,
                [
                    "data:image/png;base64,wechatmp-expired",
                    "ERROR:等待微信公众号扫码登录超时",
                    "500",
                ],
            )
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute("SELECT COUNT(*) FROM user_info").fetchone()[0]
            self.assertEqual(rows, 0)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
