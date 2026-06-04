import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from sau_mcp_server.services.models import PlatformCheckRequest, PlatformLoginRequest
from sau_mcp_server.services.platform_service import PlatformService


class PlatformServiceTests(unittest.TestCase):
    """验证共享平台 service 只负责分发，不直接绑定主线实现。"""

    def test_login_dispatches_douyin_request(self):
        service = PlatformService()
        request = PlatformLoginRequest(platform="douyin", account_name="creator", headless=True)

        with patch(
            "sau_mcp_server.services.platform_adapters.login_douyin_account",
            new=AsyncMock(return_value={"success": True, "account_file": "cookies/douyin_creator.json"}),
        ) as mock_login:
            result = asyncio.run(service.login(request))

        mock_login.assert_awaited_once_with("creator", headless=True)
        self.assertTrue(result["success"])

    def test_check_dispatches_douyin_request(self):
        service = PlatformService()
        request = PlatformCheckRequest(platform="douyin", account_name="creator")

        with patch(
            "sau_mcp_server.services.platform_adapters.check_douyin_account",
            new=AsyncMock(return_value=True),
        ) as mock_check:
            result = asyncio.run(service.check(request))

        mock_check.assert_awaited_once_with("creator")
        self.assertTrue(result)

    def test_login_raises_for_unsupported_platform(self):
        service = PlatformService()
        request = PlatformLoginRequest(platform="unknown", account_name="creator")

        with self.assertRaisesRegex(ValueError, "Unsupported platform: unknown"):
            asyncio.run(service.login(request))

    def test_login_dispatches_bilibili_request(self):
        service = PlatformService()
        request = PlatformLoginRequest(platform="bilibili", account_name="creator", headless=False)

        with patch(
            "sau_mcp_server.services.platform_adapters.login_bilibili_account",
            new=AsyncMock(return_value={"success": True, "account_file": "cookies/bilibili_creator.json"}),
        ) as mock_login:
            result = asyncio.run(service.login(request))

        mock_login.assert_awaited_once_with("creator")
        self.assertTrue(result["success"])
