import asyncio
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import sau_cli
import sau_cli_account_helpers
from sau_mcp_server.services import platform_adapters


class BilibiliCliTests(unittest.TestCase):
    """覆盖 Bilibili CLI 的命令契约与基础分发行为。"""

    def test_build_parser_accepts_bilibili_login(self):
        parser = sau_cli.build_parser()
        args = parser.parse_args(["bilibili", "login", "--account", "creator"])
        self.assertEqual(args.platform, "bilibili")
        self.assertEqual(args.action, "login")

    def test_build_parser_requires_tid_for_upload_video(self):
        parser = sau_cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "bilibili",
                    "upload-video",
                    "--account",
                    "creator",
                    "--file",
                    "demo.mp4",
                    "--title",
                    "hello",
                    "--desc",
                    "hello",
                ]
            )

    def test_dispatch_bilibili_check_prints_valid(self):
        args = Namespace(platform="bilibili", action="check", account="creator")
        with patch("sau_cli_platform_bridge.platform_service.check", new=AsyncMock(return_value=True)):
            code = asyncio.run(sau_cli.dispatch(args))
        self.assertEqual(code, 0)

    def test_login_bilibili_account_returns_friendly_message_without_terminal(self):
        with patch("sau_cli.has_interactive_terminal", return_value=False):
            result = asyncio.run(sau_cli.login_bilibili_account("creator"))
        self.assertFalse(result["success"])
        self.assertIn("local interactive terminal", result["message"].lower())
        self.assertIn("qrcode.png", result["message"].lower())

    def test_dispatch_bilibili_login_uses_platform_service(self):
        """登录分发必须复用共享 `platform_service`，避免 CLI 维护独立登录逻辑。"""

        args = Namespace(platform="bilibili", action="login", account="creator", headless=True)

        with patch(
            "sau_cli_platform_bridge.platform_service.login",
            new=AsyncMock(return_value={"success": True, "account_file": "x"}),
        ) as mock_login:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        mock_login.assert_awaited_once()

    def test_check_bilibili_account_returns_true_when_command_succeeds(self):
        """Bilibili 校验成功时应根据命令返回码返回 `True`。"""

        with patch(
            "sau_cli_account_helpers.resolve_account_file",
            return_value=Path("cookies/bilibili_creator.json"),
        ), patch(
            "sau_cli_account_helpers.run_biliup_command",
            return_value=Namespace(returncode=0),
        ) as mock_run, patch.object(Path, "exists", return_value=True):
            result = asyncio.run(sau_cli_account_helpers.check_bilibili_account("creator"))

        self.assertTrue(result)
        mock_run.assert_called_once_with(["-u", str(Path("cookies/bilibili_creator.json")), "renew"])

    def test_platform_adapters_check_bilibili_uses_account_helpers(self):
        """适配层必须直连账号 helper，不能再回跳 `sau_cli`。"""

        with patch(
            "sau_cli_account_helpers.resolve_account_file",
            return_value=Path("cookies/bilibili_creator.json"),
        ), patch(
            "sau_cli_account_helpers.run_biliup_command",
            return_value=Namespace(returncode=0),
        ) as mock_run, patch.object(Path, "exists", return_value=True):
            result = asyncio.run(platform_adapters.check_bilibili_account("creator"))

        self.assertTrue(result)
        mock_run.assert_called_once()
        mock_run.assert_called_once_with(["-u", str(Path("cookies/bilibili_creator.json")), "renew"])
