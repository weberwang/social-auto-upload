import unittest
from unittest.mock import patch

import sau_backend


class PublishEndpointTests(unittest.TestCase):
    """验证发布中心历史 Web 接口能按素材类型分流到正确上传链路。"""

    def setUp(self):
        """为每个用例创建独立测试客户端。"""
        self.client = sau_backend.app.test_client()

    def test_post_video_dispatches_douyin_note_for_image_text_content(self):
        """抖音图文发布应走图文 uploader，而不是继续误用视频链路。"""

        payload = {
            "type": 3,
            "contentType": "image_text",
            "title": "图文标题",
            "noteContent": "图文正文",
            "tags": ["图文", "测试"],
            "fileList": ["image-1.png", "image-2.png"],
            "accountList": ["douyin_creator.json"],
            "enableTimer": 0,
            "videosPerDay": 1,
            "dailyTimes": ["10:00"],
            "startDays": 0,
        }

        with patch("myUtils.web_publish.post_note_DouYin") as mock_post_note, patch(
            "myUtils.web_publish.post_video_DouYin"
        ) as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_note.assert_called_once()
        mock_post_video.assert_not_called()

    def test_post_video_rejects_image_text_for_video_only_platform(self):
        """B站当前只支持视频，收到图文请求时必须显式拒绝。"""

        payload = {
            "type": 5,
            "contentType": "image_text",
            "title": "图文标题",
            "noteContent": "图文正文",
            "tags": ["图文", "测试"],
            "fileList": ["image-1.png", "image-2.png"],
            "accountList": ["bilibili_creator.json"],
        }

        with patch("myUtils.web_publish.post_note_DouYin") as mock_post_note:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("不支持图文发布", response.get_json()["msg"])
        mock_post_note.assert_not_called()

    def test_post_video_accepts_tencent_video_with_base_and_platform_fields(self):
        """统一请求结构中的基础字段和视频号增强字段应被历史接口接受。"""

        payload = {
            "type": 2,
            "contentType": "video",
            "baseFields": {
                "title": "视频标题",
                "description": "视频简介",
                "noteContent": "",
                "tags": ["旅行"],
                "enableTimer": 1,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
            "platformFields": {
                "tencent": {
                    "collectionName": "旅行合集",
                    "declareOriginal": True,
                    "originalType": "生活",
                    "contentDeclaration": "无需声明",
                    "isDraft": True,
                }
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["tencent_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_tencent") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_video.assert_called_once()


if __name__ == "__main__":
    unittest.main()
