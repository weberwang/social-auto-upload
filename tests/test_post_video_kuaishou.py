import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from myUtils import postVideo


class KuaishouPostVideoBridgeTests(unittest.TestCase):
    """验证历史 Web 快手桥接会把平台专属字段透传到主线 uploader。"""

    def test_post_video_ks_passes_thumbnail_path_to_uploader(self):
        """快手视频桥接应把自定义封面路径传给主线视频 uploader。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("demo.mp4")]
        ), patch.object(postVideo, "_build_publish_datetimes", return_value=[datetime(2026, 6, 9, 12, 0)]), patch.object(
            postVideo, "KSVideo"
        ) as mock_uploader, patch.object(postVideo.asyncio, "run") as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_video_ks(
                "快手视频标题",
                ["demo.mp4"],
                ["测试"],
                ["creator.json"],
                thumbnail_path="cover.png",
            )

        mock_uploader.assert_called_once_with(
            title="快手视频标题",
            file_path="demo.mp4",
            tags=["测试"],
            publish_date=datetime(2026, 6, 9, 12, 0),
            account_file=Path("creator.json"),
            thumbnail_path="cover.png",
        )
        mock_run.assert_called_once_with(uploader_instance.main(), debug=False)
