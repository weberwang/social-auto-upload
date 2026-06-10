import unittest
from pathlib import Path
from unittest.mock import patch

from myUtils import postVideo


class WechatOfficialAccountPostNoteBridgeTests(unittest.TestCase):
    """验证历史 Web 微信公众号桥接会把图文请求完整透传到主线 uploader。"""

    def test_post_note_wechatmp_passes_platform_fields_to_uploader(self):
        """微信公众号图文桥接应显式传递标题、正文、图片和标签。"""

        with patch.object(postVideo, "_resolve_account_files", return_value=[Path("wechatmp_creator.json")]), patch.object(
            postVideo, "_resolve_material_files", return_value=[Path("cover.png"), Path("detail-1.png")]
        ), patch.object(postVideo, "WeChatMpArticle") as mock_uploader, patch.object(
            postVideo.asyncio, "run"
        ) as mock_run:
            uploader_instance = mock_uploader.return_value
            postVideo.post_note_wechatmp(
                "公众号图文标题",
                ["cover.png", "detail-1.png"],
                "公众号图文正文",
                ["公众号", "测试"],
                ["wechatmp_creator.json"],
            )

        mock_uploader.assert_called_once_with(
            image_paths=["cover.png", "detail-1.png"],
            title="公众号图文标题",
            note="公众号图文正文",
            tags=["公众号", "测试"],
            account_file="wechatmp_creator.json",
        )
        mock_run.assert_called_once_with(uploader_instance.main(), debug=False)
