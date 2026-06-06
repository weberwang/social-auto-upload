import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from playwright.async_api import Error as PlaywrightError

import myUtils.auth as auth


class CheckCookieTests(unittest.TestCase):
    """验证账号 Cookie 检测的异常降级行为。"""

    def test_check_cookie_returns_false_when_browser_binary_is_missing(self):
        """缺少 Playwright 浏览器时，应降级为账号校验失败而不是抛异常。"""
        missing_browser_error = PlaywrightError(
            "BrowserType.launch: Executable doesn't exist at C:/mock/headless_shell.exe"
        )

        with patch(
            "myUtils.auth.cookie_auth_douyin",
            new=AsyncMock(side_effect=missing_browser_error),
        ):
            result = asyncio.run(auth.check_cookie(3, "missing.json"))

        self.assertFalse(result)

    def test_check_cookie_reraises_other_playwright_errors(self):
        """非环境缺失类错误仍应继续抛出，避免掩盖真实业务问题。"""
        runtime_error = PlaywrightError("Target page, context or browser has been closed")

        with patch(
            "myUtils.auth.cookie_auth_douyin",
            new=AsyncMock(side_effect=runtime_error),
        ):
            with self.assertRaises(PlaywrightError):
                asyncio.run(auth.check_cookie(3, "missing.json"))

    def test_check_cookie_dispatches_bilibili_to_bridge(self):
        """B站账号校验应走 biliup 桥接，而不是落回默认 False。"""

        with patch(
            "myUtils.auth.check_bilibili_account_file",
            return_value=True,
        ) as mock_check:
            result = asyncio.run(auth.check_cookie(5, "bilibili_creator.json"))

        self.assertTrue(result)
        mock_check.assert_called_once_with("bilibili_creator.json")


if __name__ == "__main__":
    unittest.main()
