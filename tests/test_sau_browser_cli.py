import asyncio
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import sau_cli


class BrowserCliParserTests(unittest.TestCase):
    def test_build_parser_accepts_xiaohongshu_login(self):
        parser = sau_cli.build_parser()
        args = parser.parse_args(["xiaohongshu", "login", "--account", "creator"])
        self.assertEqual(args.platform, "xiaohongshu")
        self.assertEqual(args.action, "login")

    def test_upload_helpers_are_imported_for_platform_paths(self):
        """上传路径依赖的平台初始化符号必须保持可用，避免拆分后回归。"""

        self.assertTrue(hasattr(sau_cli, "douyin_setup"))
        self.assertTrue(hasattr(sau_cli, "ks_setup"))
        self.assertTrue(hasattr(sau_cli, "xiaohongshu_setup"))

    def test_douyin_upload_video_accepts_desc(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "demo.mp4"
            video_path.write_bytes(b"video")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "douyin",
                    "upload-video",
                    "--account",
                    "creator",
                    "--file",
                    str(video_path),
                    "--title",
                    "标题",
                    "--desc",
                    "视频简介",
                ]
            )

        self.assertEqual(args.desc, "视频简介")

    def test_douyin_upload_video_accepts_dual_thumbnail_aspects(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "demo.mp4"
            landscape_path = Path(tmp_dir) / "landscape.png"
            portrait_path = Path(tmp_dir) / "portrait.png"
            video_path.write_bytes(b"video")
            landscape_path.write_bytes(b"image")
            portrait_path.write_bytes(b"image")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "douyin",
                    "upload-video",
                    "--account",
                    "creator",
                    "--file",
                    str(video_path),
                    "--title",
                    "标题",
                    "--thumbnail-landscape",
                    str(landscape_path),
                    "--thumbnail-portrait",
                    str(portrait_path),
                ]
            )

        self.assertEqual(args.thumbnail_landscape, landscape_path)
        self.assertEqual(args.thumbnail_portrait, portrait_path)

    def test_tencent_upload_video_accepts_dual_thumbnail_aspects(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "demo.mp4"
            landscape_path = Path(tmp_dir) / "landscape.png"
            portrait_path = Path(tmp_dir) / "portrait.png"
            video_path.write_bytes(b"video")
            landscape_path.write_bytes(b"image")
            portrait_path.write_bytes(b"image")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "tencent",
                    "upload-video",
                    "--account",
                    "creator",
                    "--file",
                    str(video_path),
                    "--title",
                    "标题",
                    "--thumbnail-landscape",
                    str(landscape_path),
                    "--thumbnail-portrait",
                    str(portrait_path),
                ]
            )

        self.assertEqual(args.thumbnail_landscape, landscape_path)
        self.assertEqual(args.thumbnail_portrait, portrait_path)

    def test_kuaishou_upload_note_accepts_title_and_note(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "1.png"
            image_path.write_bytes(b"image")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "kuaishou",
                    "upload-note",
                    "--account",
                    "creator",
                    "--images",
                    str(image_path),
                    "--title",
                    "图文标题",
                    "--note",
                    "图文正文",
                ]
            )

        self.assertEqual(args.title, "图文标题")
        self.assertEqual(args.note, "图文正文")

    def test_xiaohongshu_upload_video_defaults_to_headless(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video_path = Path(tmp_dir) / "demo.mp4"
            video_path.write_bytes(b"video")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "xiaohongshu",
                    "upload-video",
                    "--account",
                    "creator",
                    "--file",
                    str(video_path),
                    "--title",
                    "视频标题",
                ]
            )

        self.assertTrue(args.headless)

    def test_xiaohongshu_upload_note_accepts_headed(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = Path(tmp_dir) / "1.png"
            image_path.write_bytes(b"image")

            parser = sau_cli.build_parser()
            args = parser.parse_args(
                [
                    "xiaohongshu",
                    "upload-note",
                    "--account",
                    "creator",
                    "--images",
                    str(image_path),
                    "--title",
                    "图文标题",
                    "--note",
                    "图文正文",
                    "--headed",
                ]
            )

        self.assertFalse(args.headless)


class BrowserCliDispatchTests(unittest.TestCase):
    """覆盖浏览器类平台 CLI 的基础分发行为。"""

    def test_dispatch_douyin_login_uses_platform_service(self):
        args = Namespace(
            platform="douyin",
            action="login",
            account="creator",
            headless=False,
        )
        with patch(
            "sau_cli_platform_bridge.platform_service.login",
            new=AsyncMock(return_value={"success": True, "account_file": "cookies/douyin_creator.json"}),
        ) as mock_login:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        request = mock_login.await_args.args[0]
        self.assertEqual(request.platform, "douyin")
        self.assertEqual(request.account_name, "creator")
        self.assertFalse(request.headless)

    def test_dispatch_douyin_check_uses_platform_service(self):
        args = Namespace(platform="douyin", action="check", account="creator")
        with patch("sau_cli_platform_bridge.platform_service.check", new=AsyncMock(return_value=True)) as mock_check:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        request = mock_check.await_args.args[0]
        self.assertEqual(request.platform, "douyin")
        self.assertEqual(request.account_name, "creator")

    def test_dispatch_xiaohongshu_check_prints_valid(self):
        args = Namespace(platform="xiaohongshu", action="check", account="creator")
        with patch("sau_cli_platform_bridge.platform_service.check", new=AsyncMock(return_value=True)):
            code = asyncio.run(sau_cli.dispatch(args))
        self.assertEqual(code, 0)

    def test_dispatch_tencent_login_still_uses_local_helper(self):
        """Tencent 登录暂不接入共享 service，避免越过当前任务边界。"""

        args = Namespace(platform="tencent", action="login", account="creator", headless=True)

        with patch(
            "sau_cli_platform_bridge.platform_service.login",
            new=AsyncMock(return_value={"success": True, "account_file": "x"}),
        ) as mock_service_login, patch(
            "sau_cli.login_tencent_account",
            new=AsyncMock(return_value={"success": True, "account_file": "legacy"}),
        ) as mock_local_login:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        mock_local_login.assert_awaited_once()
        mock_service_login.assert_not_awaited()

    def test_dispatch_tencent_check_still_uses_local_helper(self):
        """Tencent 校验暂不接入共享 service，避免越过当前任务边界。"""

        args = Namespace(platform="tencent", action="check", account="creator")

        with patch(
            "sau_cli_platform_bridge.platform_service.check",
            new=AsyncMock(return_value=True),
        ) as mock_service_check, patch(
            "sau_cli.check_tencent_account",
            new=AsyncMock(return_value=True),
        ) as mock_local_check:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        mock_local_check.assert_awaited_once()
        mock_service_check.assert_not_awaited()

    def test_dispatch_douyin_upload_note_uses_new_request_fields(self):
        args = Namespace(
            platform="douyin",
            action="upload-note",
            account="creator",
            images=[Path("1.png")],
            title="图文标题",
            note="图文正文",
            tags="测试,图文",
            schedule=0,
            debug=False,
            headless=True,
        )
        with patch("sau_cli.upload_note", new=AsyncMock()) as mock_upload:
            asyncio.run(sau_cli.dispatch(args))

        request = mock_upload.await_args.args[0]
        self.assertEqual(request.title, "图文标题")
        self.assertEqual(request.note, "图文正文")

    def test_dispatch_douyin_upload_video_uses_dual_thumbnail_request_fields(self):
        args = Namespace(
            platform="douyin",
            action="upload-video",
            account="creator",
            file=Path("demo.mp4"),
            title="视频标题",
            desc="视频简介",
            tags="测试,视频",
            schedule=0,
            thumbnail=None,
            thumbnail_landscape=Path("landscape.png"),
            thumbnail_portrait=Path("portrait.png"),
            product_link="",
            product_title="",
            debug=False,
            headless=True,
        )
        with patch("sau_cli.upload_video", new=AsyncMock()) as mock_upload:
            asyncio.run(sau_cli.dispatch(args))

        request = mock_upload.await_args.args[0]
        self.assertEqual(request.thumbnail_landscape_file, Path("landscape.png"))
        self.assertEqual(request.thumbnail_portrait_file, Path("portrait.png"))

    def test_dispatch_tencent_upload_video_uses_dual_thumbnail_request_fields(self):
        args = Namespace(
            platform="tencent",
            action="upload-video",
            account="creator",
            file=Path("demo.mp4"),
            title="视频标题",
            desc="视频简介",
            tags="测试,视频",
            schedule=0,
            thumbnail=None,
            thumbnail_landscape=Path("landscape.png"),
            thumbnail_portrait=Path("portrait.png"),
            short_title=None,
            category=None,
            draft=False,
            debug=False,
            headless=True,
        )
        with patch("sau_cli.upload_tencent_video", new=AsyncMock()) as mock_upload:
            asyncio.run(sau_cli.dispatch(args))

        request = mock_upload.await_args.args[0]
        self.assertEqual(request.thumbnail_landscape_file, Path("landscape.png"))
        self.assertEqual(request.thumbnail_portrait_file, Path("portrait.png"))

    def test_dispatch_xiaohongshu_upload_video_uses_headed_request(self):
        args = Namespace(
            platform="xiaohongshu",
            action="upload-video",
            account="creator",
            file=Path("demo.mp4"),
            title="视频标题",
            desc="视频简介",
            tags="测试,视频",
            schedule=0,
            thumbnail=None,
            debug=False,
            headless=False,
        )
        with patch("sau_cli.upload_xiaohongshu_video", new=AsyncMock()) as mock_upload:
            asyncio.run(sau_cli.dispatch(args))

        request = mock_upload.await_args.args[0]
        self.assertEqual(request.title, "视频标题")
        self.assertEqual(request.description, "视频简介")
        self.assertFalse(request.headless)

    def test_dispatch_xiaohongshu_upload_note_uses_headless_request(self):
        args = Namespace(
            platform="xiaohongshu",
            action="upload-note",
            account="creator",
            images=[Path("1.png"), Path("2.png")],
            title="图文标题",
            note="图文正文",
            tags="测试,图文",
            schedule=0,
            debug=False,
            headless=True,
        )
        with patch("sau_cli.upload_xiaohongshu_note", new=AsyncMock()) as mock_upload:
            asyncio.run(sau_cli.dispatch(args))

        request = mock_upload.await_args.args[0]
        self.assertEqual(request.title, "图文标题")
        self.assertEqual(request.note, "图文正文")
        self.assertTrue(request.headless)
        self.assertEqual(len(request.image_files), 2)


class SauCliServiceIntegrationTests(unittest.TestCase):
    """验证 CLI 入口直接复用共享平台 service。"""

    def test_dispatch_login_uses_platform_service(self):
        """登录分发必须走共享 `platform_service`，避免 CLI 维护独立业务逻辑。"""

        args = Namespace(platform="douyin", action="login", account="creator", headless=True)

        with patch(
            "sau_cli_platform_bridge.platform_service.login",
            new=AsyncMock(return_value={"success": True, "account_file": "x"}),
        ) as mock_login:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        mock_login.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
