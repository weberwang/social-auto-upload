from __future__ import annotations

import tempfile
import unittest
import types
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from myUtils import bilibili_web_bridge


class BilibiliWebBridgeTests(unittest.TestCase):
    """验证历史 Web 到 B 站主线能力的桥接参数拼装。"""

    def test_resolve_bilibili_account_path_prefers_legacy_cookie_dir(self) -> None:
        """如果历史 Web 目录已有同名账号文件，应优先复用该文件。"""

        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            legacy_dir = base_dir / "cookiesFile"
            mainline_dir = base_dir / "cookies"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            mainline_dir.mkdir(parents=True, exist_ok=True)

            legacy_path = legacy_dir / "bilibili_creator.json"
            mainline_path = mainline_dir / "bilibili_creator.json"
            legacy_path.write_text("legacy", encoding="utf-8")
            mainline_path.write_text("mainline", encoding="utf-8")

            with patch.object(bilibili_web_bridge, "BASE_DIR", base_dir):
                resolved = bilibili_web_bridge.resolve_bilibili_account_path("bilibili_creator.json")

        self.assertEqual(resolved, legacy_path)

    def test_check_bilibili_account_file_uses_cookie_login(self) -> None:
        """B 站账号校验应直接验证当前 cookie，而不是错误地依赖 renew 续期。"""

        fake_module = types.ModuleType("biliup.plugins.bili_webup")

        class FakeBiliClient:
            def __init__(self, *_args, **_kwargs) -> None:
                self.payload = None

            def login_by_cookies(self, payload) -> None:
                self.payload = payload

        fake_module.BiliBili = FakeBiliClient
        fake_module.Data = lambda: object()

        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            cookie_dir = base_dir / "cookiesFile"
            cookie_dir.mkdir(parents=True, exist_ok=True)
            account_path = cookie_dir / "bilibili_creator.json"
            account_path.write_text('{"SESSDATA":"sess","bili_jct":"csrf"}', encoding="utf-8")

            with patch.object(bilibili_web_bridge, "BASE_DIR", base_dir), patch.dict(
                "sys.modules",
                {"biliup.plugins.bili_webup": fake_module},
            ):
                result = bilibili_web_bridge.check_bilibili_account_file("bilibili_creator.json")

        self.assertTrue(result)

    def test_build_biliup_account_payload_fills_required_token_fields(self) -> None:
        """旧扁平账号文件应被补齐成 CLI 上传所需的 token 字段。"""

        payload = bilibili_web_bridge.build_biliup_account_payload({
            "SESSDATA": "sess",
            "bili_jct": "csrf",
            "DedeUserID": "470501430",
            "access_token": "access",
            "refresh_token": "refresh",
        })

        self.assertEqual(payload["token_info"]["expires_in"], 0)
        self.assertEqual(payload["token_info"]["mid"], 470501430)
        self.assertEqual(payload["cookie_info"]["domains"], [".bilibili.com"])
        self.assertEqual(payload["sso"], [])
        self.assertEqual(payload["platform"], "Android")

    def test_post_video_bilibili_builds_upload_command_with_schedule(self) -> None:
        """历史 Web 发布桥接应把标题、简介、分区、标签和定时参数全部带给 biliup。"""

        schedule_time = datetime(2026, 6, 7, 10, 0)

        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            (base_dir / "cookiesFile").mkdir(parents=True, exist_ok=True)
            (base_dir / "videoFile").mkdir(parents=True, exist_ok=True)
            account_path = base_dir / "cookiesFile" / "bilibili_creator.json"
            video_path = base_dir / "videoFile" / "demo.mp4"
            account_path.write_text(
                '{"SESSDATA":"sess","bili_jct":"csrf","access_token":"access","refresh_token":"refresh"}',
                encoding="utf-8",
            )
            video_path.write_text("video", encoding="utf-8")

            with patch.object(bilibili_web_bridge, "BASE_DIR", base_dir), patch(
                "myUtils.bilibili_web_bridge.generate_schedule_time_next_day",
                return_value=[schedule_time],
            ), patch(
                "myUtils.bilibili_web_bridge.run_biliup_command",
                return_value=Namespace(returncode=0, stdout="", stderr=""),
            ) as mock_run:
                bilibili_web_bridge.post_video_bilibili(
                    title="测试标题",
                    files=["demo.mp4"],
                    tags=["测试", "足球"],
                    account_files=["bilibili_creator.json"],
                    tid=249,
                    description="测试简介",
                    enableTimer=True,
                    videos_per_day=1,
                    daily_times=["10:00"],
                    start_days=0,
                )

        called_arguments = mock_run.call_args.args[0]
        self.assertEqual(called_arguments[0], "-u")
        self.assertNotEqual(called_arguments[1], str(account_path))
        self.assertEqual(
            called_arguments[2:],
            [
                "upload",
                str(video_path),
                "--title",
                "测试标题",
                "--desc",
                "测试简介",
                "--tid",
                "249",
                "--tag",
                "测试,足球",
                "--dtime",
                str(int(schedule_time.timestamp())),
            ],
        )


if __name__ == "__main__":
    unittest.main()
