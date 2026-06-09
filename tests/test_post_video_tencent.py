import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from myUtils import postVideo


class TencentPostVideoBridgeTests(unittest.TestCase):
    """验证历史 Web 视频号桥接会把平台专属字段完整透传到主线 uploader。"""

    def test_post_video_tencent_passes_platform_fields_to_uploader(self):
        """视频号视频桥接应把短标题、合集、原创声明和封面字段一起传给主线视频 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("demo.mp4")]
        ), patch.object(postVideo, "_build_publish_datetimes", return_value=[datetime(2026, 6, 9, 12, 0)]), patch.object(
            postVideo, "TencentVideo"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_video_tencent(
                "视频号视频标题",
                ["demo.mp4"],
                ["测试"],
                ["creator.json"],
                enableTimer=False,
                is_draft=True,
                short_title="短标题",
                thumbnail_landscape_path="landscape.png",
                thumbnail_portrait_path="portrait.png",
                collection_name="旅行合集",
                declare_original=True,
                original_type="生活",
                content_declaration="无需声明",
            )

        mock_uploader.assert_called_once_with(
            title="视频号视频标题",
            file_path="demo.mp4",
            tags=["测试"],
            publish_date=datetime(2026, 6, 9, 12, 0),
            account_file=Path("creator.json"),
            category="生活",
            is_draft=True,
            thumbnail_path=None,
            thumbnail_landscape_path="landscape.png",
            thumbnail_portrait_path="portrait.png",
            short_title="短标题",
        )
        self.assertEqual(uploader_instance.collection_name, "旅行合集")
        self.assertTrue(uploader_instance.declare_original)
        self.assertEqual(uploader_instance.original_type, "生活")
        self.assertEqual(uploader_instance.content_declaration, "无需声明")
        mock_run.assert_called_once_with(uploader_instance.main(), debug=False)
