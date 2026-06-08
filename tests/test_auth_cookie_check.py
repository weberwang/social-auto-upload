import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from playwright.async_api import Error as PlaywrightError

conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.DEBUG_MODE = True
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
conf_stub.XHS_SERVER = "http://127.0.0.1:11901"
sys.modules["conf"] = conf_stub


def _load_auth_module():
    """为每个用例重载认证模块，避免前序测试残留的模块实例污染当前补丁目标。"""

    sys.modules.pop("myUtils.auth", None)
    return importlib.import_module("myUtils.auth")


class CheckCookieTests(unittest.TestCase):
    """验证账号 Cookie 校验流程的异常降级与分发逻辑。"""

    def setUp(self):
        """准备当前用例独享的 auth 模块实例，确保 patch 命中真实调用对象。"""

        self.auth = _load_auth_module()

    def test_check_cookie_returns_false_when_browser_binary_is_missing(self):
        """缺少 Playwright 浏览器时，应降级为账号校验失败而不是抛异常。"""

        missing_browser_error = PlaywrightError(
            "BrowserType.launch: Executable doesn't exist at C:/mock/headless_shell.exe"
        )

        with patch.object(
            self.auth,
            "cookie_auth_douyin",
            new=AsyncMock(side_effect=missing_browser_error),
        ):
            result = asyncio.run(self.auth.check_cookie(3, "missing.json"))

        self.assertFalse(result)

    def test_check_cookie_reraises_other_playwright_errors(self):
        """非环境缺失类错误仍应继续抛出，避免掩盖真实业务问题。"""

        runtime_error = PlaywrightError("Target page, context or browser has been closed")

        with patch.object(
            self.auth,
            "cookie_auth_douyin",
            new=AsyncMock(side_effect=runtime_error),
        ):
            with self.assertRaises(PlaywrightError):
                asyncio.run(self.auth.check_cookie(3, "missing.json"))

    def test_check_cookie_dispatches_bilibili_to_bridge(self):
        """B 站账号校验应走 biliup 桥接，而不是落回默认 False。"""

        with patch.object(
            self.auth,
            "check_bilibili_account_file",
            return_value=True,
        ) as mock_check:
            result = asyncio.run(self.auth.check_cookie(5, "bilibili_creator.json"))

        self.assertTrue(result)
        mock_check.assert_called_once_with("bilibili_creator.json")

    def test_check_cookie_dispatches_tencent_to_mainline_validator(self):
        """视频号账号校验应复用主线校验器，避免登录与账号列表走两套浏览器策略。"""

        with patch.object(
            self.auth,
            "mainline_tencent_cookie_auth",
            new=AsyncMock(return_value=True),
        ) as mock_check:
            result = asyncio.run(self.auth.check_cookie(2, "tencent_creator.json"))

        self.assertTrue(result)
        mock_check.assert_awaited_once()
        called_account_file = mock_check.await_args.args[0]
        self.assertTrue(str(called_account_file).endswith("cookiesFile\\tencent_creator.json"))

    def test_check_cookie_dispatches_douyin_to_mainline_validator(self):
        """抖音账号校验应复用主线校验器，避免成功登录后又被旧校验逻辑误判。"""

        with patch.object(
            self.auth,
            "mainline_douyin_cookie_auth",
            new=AsyncMock(return_value=True),
        ) as mock_check:
            result = asyncio.run(self.auth.check_cookie(3, "douyin_creator.json"))

        self.assertTrue(result)
        mock_check.assert_awaited_once()
        called_account_file = mock_check.await_args.args[0]
        self.assertTrue(str(called_account_file).endswith("cookiesFile\\douyin_creator.json"))


if __name__ == "__main__":
    unittest.main()
