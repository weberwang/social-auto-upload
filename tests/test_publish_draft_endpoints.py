import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sau_backend import app


def build_publish_workspace() -> dict[str, object]:
    """构造发布中心草稿测试数据，覆盖多 Tab 与素材字段回填场景。"""

    return {
        "activeTab": "tab2",
        "tabCounter": 2,
        "tabs": [
            {
                "name": "tab1",
                "label": "发布1",
                "selectedPlatform": 3,
                "contentType": "video",
                "title": "第一个标题",
                "description": "",
                "noteContent": "",
                "selectedTopics": ["游戏"],
                "selectedAccounts": [1],
                "scheduleEnabled": False,
                "videosPerDay": 1,
                "dailyTimes": ["10:00"],
                "startDays": 0,
                "isDraft": False,
                "isOriginal": False,
                "fileList": [
                    {
                        "name": "video.mp4",
                        "path": "video.mp4",
                        "size": 123,
                        "url": "http://localhost/video.mp4",
                    }
                ],
            },
            {
                "name": "tab2",
                "label": "发布2",
                "selectedPlatform": 1,
                "contentType": "image_text",
                "title": "第二个标题",
                "description": "",
                "noteContent": "图文正文",
                "selectedTopics": ["旅行"],
                "selectedAccounts": [2],
                "scheduleEnabled": True,
                "videosPerDay": 2,
                "dailyTimes": ["10:00", "18:00"],
                "startDays": 1,
                "isDraft": False,
                "isOriginal": True,
                "fileList": [
                    {
                        "name": "image-1.png",
                        "path": "image-1.png",
                        "size": 66,
                        "url": "http://localhost/image-1.png",
                    }
                ],
            },
        ],
    }


class PublishDraftEndpointTests(unittest.TestCase):
    """验证发布中心草稿接口可以完成保存、列表、加载与删除。"""

    def setUp(self):
        """为每个用例准备隔离的临时目录与测试客户端。"""

        self.client = app.test_client()
        self.base_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """清理测试目录，避免草稿数据库互相污染。"""

        shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_save_publish_draft_creates_table_and_returns_draft_id(self):
        """保存草稿时应自动补齐数据表，并把工作区快照持久化。"""

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.post(
                "/savePublishDraft",
                json={
                    "name": "测试草稿",
                    "workspace": build_publish_workspace(),
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)
        self.assertIsInstance(payload["data"]["id"], int)

        with sqlite3.connect(self.base_dir / "db" / "database.db") as conn:
            row = conn.execute(
                "SELECT name, payload FROM publish_drafts WHERE id = ?",
                (payload["data"]["id"],),
            ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "测试草稿")
        self.assertEqual(json.loads(row[1]), build_publish_workspace())

    def test_get_publish_drafts_and_detail_return_saved_workspace(self):
        """列表接口与详情接口都应返回最近保存的草稿内容。"""

        with patch("sau_backend.BASE_DIR", self.base_dir):
            save_response = self.client.post(
                "/savePublishDraft",
                json={
                    "name": "待加载草稿",
                    "workspace": build_publish_workspace(),
                },
            )
            draft_id = save_response.get_json()["data"]["id"]

            list_response = self.client.get("/getPublishDrafts")
            detail_response = self.client.get(f"/getPublishDraft?id={draft_id}")

        self.assertEqual(list_response.status_code, 200)
        list_payload = list_response.get_json()
        self.assertEqual(list_payload["code"], 200)
        self.assertEqual(len(list_payload["data"]), 1)
        self.assertEqual(list_payload["data"][0]["name"], "待加载草稿")

        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.get_json()
        self.assertEqual(detail_payload["code"], 200)
        self.assertEqual(detail_payload["data"]["id"], draft_id)
        self.assertEqual(detail_payload["data"]["workspace"], build_publish_workspace())

    def test_delete_publish_draft_removes_saved_record(self):
        """删除草稿后，列表与数据库里都不应再保留该记录。"""

        with patch("sau_backend.BASE_DIR", self.base_dir):
            save_response = self.client.post(
                "/savePublishDraft",
                json={
                    "name": "待删除草稿",
                    "workspace": build_publish_workspace(),
                },
            )
            draft_id = save_response.get_json()["data"]["id"]

            delete_response = self.client.get(f"/deletePublishDraft?id={draft_id}")
            list_response = self.client.get("/getPublishDrafts")

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.get_json()["code"], 200)
        self.assertEqual(list_response.get_json()["data"], [])

        with sqlite3.connect(self.base_dir / "db" / "database.db") as conn:
            row_count = conn.execute("SELECT COUNT(*) FROM publish_drafts").fetchone()[0]

        self.assertEqual(row_count, 0)


if __name__ == "__main__":
    unittest.main()
