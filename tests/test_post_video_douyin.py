import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from myUtils import postVideo


class DouyinPostVideoBridgeTests(unittest.TestCase):
    """验证历史 Web 抖音桥接会把平台专属字段完整透传到主线 uploader。"""

    def test_post_video_douyin_passes_platform_fields_to_uploader(self):
        """抖音视频桥接应把商品、位置、自主声明和同步开关一起传给主线视频 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("demo.mp4")]
        ), patch.object(postVideo, "_build_publish_datetimes", return_value=[datetime(2026, 6, 9, 12, 0)]), patch.object(
            postVideo, "DouYinVideo"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_video_DouYin(
                "视频标题",
                ["demo.mp4"],
                ["测试"],
                ["creator.json"],
                enableTimer=False,
                thumbnail_path="portrait.png",
                productLink="https://example.com/item",
                productTitle="示例商品",
                location="上海市",
                self_declaration="内容为个人观点或见解",
                sync_to_toutiao_xigua=False,
            )

        mock_uploader.assert_called_once_with(
            title="视频标题",
            file_path="demo.mp4",
            tags=["测试"],
            publish_date=datetime(2026, 6, 9, 12, 0),
            account_file=Path("creator.json"),
            thumbnail_portrait_path="portrait.png",
            productLink="https://example.com/item",
            productTitle="示例商品",
            desc="视频标题",
            location="上海市",
            self_declaration="内容为个人观点或见解",
            sync_to_toutiao_xigua=False,
        )
        mock_run.assert_called_once_with(uploader_instance.douyin_upload_video(), debug=False)

    def test_post_note_douyin_passes_platform_fields_to_uploader(self):
        """抖音图文桥接应把位置和自主声明透传给主线图文 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("1.png"), Path("2.png")]
        ), patch.object(postVideo, "_build_single_publish_datetime", return_value=datetime(2026, 6, 9, 18, 0)), patch.object(
            postVideo, "DouYinNote"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_note_DouYin(
                "图文标题",
                ["1.png", "2.png"],
                "图文正文",
                ["探店"],
                ["creator.json"],
                location="杭州市",
                self_declaration="内容为个人观点或见解",
            )

        mock_uploader.assert_called_once_with(
            image_paths=["1.png", "2.png"],
            title="图文标题",
            note="图文正文",
            tags=["探店"],
            publish_date=datetime(2026, 6, 9, 18, 0),
            account_file="creator.json",
            location="杭州市",
            self_declaration="内容为个人观点或见解",
        )
        mock_run.assert_called_once_with(uploader_instance.douyin_upload_note(), debug=False)
