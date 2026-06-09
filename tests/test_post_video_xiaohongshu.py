import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from myUtils import postVideo


class XiaohongshuPostVideoBridgeTests(unittest.TestCase):
    """验证历史 Web 小红书桥接会把平台专属字段透传到主线 uploader。"""

    def test_post_video_xhs_passes_platform_fields_to_uploader(self):
        """小红书视频桥接应把封面和位置传给主线视频 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("demo.mp4")]
        ), patch.object(postVideo, "_build_publish_datetimes", return_value=[datetime(2026, 6, 9, 12, 0)]), patch.object(
            postVideo, "XiaoHongShuVideo"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_video_xhs(
                "小红书视频标题",
                ["demo.mp4"],
                ["测试"],
                ["creator.json"],
                thumbnail_path="cover.png",
                location="上海市",
            )

        mock_uploader.assert_called_once_with(
            title="小红书视频标题",
            file_path=Path("demo.mp4"),
            tags=["测试"],
            publish_date=datetime(2026, 6, 9, 12, 0),
            account_file=Path("creator.json"),
            thumbnail_path="cover.png",
            location="上海市",
        )
        mock_run.assert_called_once_with(uploader_instance.main(), debug=False)

    def test_post_note_xhs_passes_location_to_uploader(self):
        """小红书图文桥接应把位置传给主线图文 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("1.png"), Path("2.png")]
        ), patch.object(postVideo, "_build_single_publish_datetime", return_value=datetime(2026, 6, 9, 18, 0)), patch.object(
            postVideo, "XiaoHongShuNote"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_note_xhs(
                "小红书图文标题",
                ["1.png", "2.png"],
                "图文正文",
                ["探店"],
                ["creator.json"],
                location="杭州市",
            )

        mock_uploader.assert_called_once_with(
            image_paths=["1.png", "2.png"],
            title="小红书图文标题",
            note="图文正文",
            desc="图文正文",
            tags=["探店"],
            publish_date=datetime(2026, 6, 9, 18, 0),
            account_file="creator.json",
            location="杭州市",
        )
        mock_run.assert_called_once_with(uploader_instance.main(), debug=False)
