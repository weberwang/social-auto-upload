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

    def test_post_video_dispatches_wechatmp_note_for_image_text_content(self):
        """微信公众号图文发布应走独立图文 uploader，避免误落到其他平台链路。"""

        payload = {
            "type": 6,
            "contentType": "image_text",
            "baseFields": {
                "title": "公众号图文标题",
                "noteContent": "公众号图文正文",
                "tags": ["公众号", "测试"],
            },
            "fileList": ["cover.png", "detail-1.png"],
            "accountList": ["wechatmp_creator.json"],
        }

        with patch("myUtils.web_publish.post_note_wechatmp") as mock_post_note:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_note.assert_called_once_with(
            "公众号图文标题",
            ["cover.png", "detail-1.png"],
            "公众号图文正文",
            ["公众号", "测试"],
            ["wechatmp_creator.json"],
        )

    def test_post_video_rejects_wechatmp_video_request(self):
        """微信公众号当前只支持图文，收到视频请求时必须明确拒绝。"""

        payload = {
            "type": 6,
            "contentType": "video",
            "baseFields": {
                "title": "公众号视频标题",
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["wechatmp_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_tencent") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("仅支持图文发布", response.get_json()["msg"])
        mock_post_video.assert_not_called()

    def test_post_video_rejects_wechatmp_scheduled_image_text_request(self):
        """微信公众号当前不支持定时发布，避免前端误以为定时配置已经生效。"""

        payload = {
            "type": 6,
            "contentType": "image_text",
            "baseFields": {
                "title": "公众号图文标题",
                "noteContent": "公众号图文正文",
                "enableTimer": 1,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
            "fileList": ["cover.png"],
            "accountList": ["wechatmp_creator.json"],
        }

        with patch("myUtils.web_publish.post_note_wechatmp") as mock_post_note:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("不支持定时发布", response.get_json()["msg"])
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
        self.assertEqual(
            mock_post_video.call_args.args,
            (
                "视频标题",
                ["video-a.mp4"],
                ["旅行"],
                ["tencent_creator.json"],
                None,
                1,
                1,
                ["10:00"],
                0,
                True,
                "",
                "",
                "",
                "",
                "旅行合集",
                True,
                "生活",
                "无需声明",
            ),
        )

    def test_post_video_accepts_xiaohongshu_video_platform_fields(self):
        """小红书视频增强字段应透传到历史发布入口，避免封面和位置在旧接口层丢失。"""

        payload = {
            "type": 1,
            "contentType": "video",
            "baseFields": {
                "title": "小红书视频标题",
                "description": "小红书视频简介",
                "tags": ["探店"],
                "enableTimer": 0,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
            "platformFields": {
                "xiaohongshu": {
                    "thumbnailPath": "cover.png",
                    "location": "上海市",
                }
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["xiaohongshu_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_xhs") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_video.assert_called_once()
        self.assertEqual(
            mock_post_video.call_args.args,
            (
                "小红书视频标题",
                ["video-a.mp4"],
                ["探店"],
                ["xiaohongshu_creator.json"],
                None,
                0,
                1,
                ["10:00"],
                0,
                "cover.png",
                "上海市",
            ),
        )

    def test_post_video_accepts_bilibili_video_platform_fields(self):
        """B站视频增强字段应透传到历史发布入口，避免结构化 payload 丢失简介和分区。"""

        payload = {
            "type": 5,
            "contentType": "video",
            "baseFields": {
                "title": "B站视频标题",
                "description": "",
                "tags": ["测评"],
                "enableTimer": 1,
                "videosPerDay": 2,
                "dailyTimes": ["10:00", "18:00"],
                "startDays": 1,
            },
            "platformFields": {
                "bilibili": {
                    "description": "B站视频简介",
                    "tid": 17,
                }
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["bilibili_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_bilibili") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_video.assert_called_once()
        self.assertEqual(
            mock_post_video.call_args.args,
            (
                "B站视频标题",
                ["video-a.mp4"],
                ["测评"],
                ["bilibili_creator.json"],
                17,
            ),
        )
        self.assertEqual(
            mock_post_video.call_args.kwargs,
            {
                "description": "B站视频简介",
                "enableTimer": 1,
                "videos_per_day": 2,
                "daily_times": ["10:00", "18:00"],
                "start_days": 1,
            },
        )


    def test_post_video_accepts_douyin_video_platform_fields(self):
        """抖音视频增强字段应透传到历史发布入口，避免新增字段在旧接口层丢失。"""

        payload = {
            "type": 3,
            "contentType": "video",
            "baseFields": {
                "title": "视频标题",
                "description": "视频简介",
                "tags": ["探店"],
                "enableTimer": 0,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
            "platformFields": {
                "douyin": {
                    "productTitle": "示例商品",
                    "productLink": "https://example.com/item",
                    "location": "上海市",
                    "selfDeclaration": "内容为个人观点或见解",
                    "syncToToutiaoXigua": False,
                }
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["douyin_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_DouYin") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_video.assert_called_once()
        self.assertEqual(
            mock_post_video.call_args.args,
            (
                "视频标题",
                ["video-a.mp4"],
                ["探店"],
                ["douyin_creator.json"],
                None,
                0,
                1,
                ["10:00"],
                0,
                "",
                "https://example.com/item",
                "示例商品",
                "上海市",
                "内容为个人观点或见解",
                False,
            ),
        )

    def test_post_video_accepts_kuaishou_video_platform_fields(self):
        """快手视频增强字段应透传到历史发布入口，避免自定义封面在旧接口层丢失。"""

        payload = {
            "type": 4,
            "contentType": "video",
            "baseFields": {
                "title": "快手视频标题",
                "description": "快手视频简介",
                "tags": ["探店"],
                "enableTimer": 0,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
            },
            "platformFields": {
                "kuaishou": {
                    "thumbnailPath": "cover.png",
                }
            },
            "fileList": ["video-a.mp4"],
            "accountList": ["kuaishou_creator.json"],
        }

        with patch("myUtils.web_publish.post_video_ks") as mock_post_video:
            response = self.client.post("/postVideo", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["code"], 200)
        mock_post_video.assert_called_once()
        self.assertEqual(
            mock_post_video.call_args.args,
            (
                "快手视频标题",
                ["video-a.mp4"],
                ["探店"],
                ["kuaishou_creator.json"],
                None,
                0,
                1,
                ["10:00"],
                0,
                "cover.png",
            ),
        )


if __name__ == "__main__":
    unittest.main()
