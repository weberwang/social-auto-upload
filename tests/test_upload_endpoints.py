import sqlite3
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from sau_backend import app


class UploadEndpointTests(unittest.TestCase):
    """验证上传接口在目标目录缺失时会自动补齐目录并完成保存。"""

    def setUp(self):
        """为每个用例准备独立的临时工作目录和测试客户端。"""
        self.client = app.test_client()
        self.base_dir = Path(tempfile.mkdtemp())
        self._prepare_database()

    def tearDown(self):
        """清理临时目录，避免测试之间互相污染。"""
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def test_upload_creates_video_directory_before_saving_file(self):
        """`/upload` 在 `videoFile` 缺失时也应自动创建目录并保存文件。"""
        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.post(
                "/upload",
                data={"file": (BytesIO(b"video-bytes"), "sample.mp4")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)

        saved_path = self.base_dir / "videoFile" / payload["data"]
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.read_bytes(), b"video-bytes")

    def test_upload_save_creates_video_directory_and_persists_record(self):
        """`/uploadSave` 需要同时完成文件保存、真实文件名保留和备注写入。"""
        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.post(
                "/uploadSave",
                data={
                    "file": (BytesIO(b"video-bytes"), "sample.mp4"),
                    "remark": "首页主视觉素材",
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)

        saved_path = self.base_dir / "videoFile" / payload["data"]["filepath"]
        self.assertTrue(saved_path.exists())

        with sqlite3.connect(self.base_dir / "db" / "database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT filename, file_path, remark FROM file_records WHERE file_path = ?",
                (payload["data"]["filepath"],),
            )
            record = cursor.fetchone()

        self.assertEqual(record, ("sample.mp4", payload["data"]["filepath"], "首页主视觉素材"))

    def test_download_material_returns_attachment_response(self):
        """素材下载接口应以附件形式返回已上传文件，供预览弹窗回退下载。"""
        file_name = "preview.txt"
        material_dir = self.base_dir / "videoFile"
        material_dir.mkdir(parents=True, exist_ok=True)
        (material_dir / file_name).write_text("preview content", encoding="utf-8")

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.get(f"/download/{file_name}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response.headers.get("Content-Disposition", ""))
        self.assertEqual(response.data, b"preview content")

    def test_get_files_returns_pagination_metadata_for_material_management(self):
        """素材管理分页查询应返回当前页数据以及总数元信息。"""
        self._insert_material_record("older.mp4", 2.1, "2026-06-01 09:00:00", "uuid_older.mp4")
        self._insert_material_record("middle.jpg", 3.2, "2026-06-02 09:00:00", "uuid_middle.jpg")
        self._insert_material_record("latest.mp4", 4.3, "2026-06-03 09:00:00", "uuid_latest.mp4")

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.get(
                "/getFiles?page=2&page_size=1&sort_by=upload_time&sort_order=desc",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["pagination"], {
            "page": 2,
            "page_size": 1,
            "total": 3,
            "total_pages": 3,
        })
        self.assertEqual([item["filename"] for item in payload["data"]], ["middle.jpg"])

    def test_get_files_supports_keyword_type_and_size_sort_filters(self):
        """素材管理分页查询应支持关键字、类型过滤和按大小排序。"""
        self._insert_material_record("cover-small.jpg", 1.5, "2026-06-01 09:00:00", "uuid_cover_small.jpg")
        self._insert_material_record("cover-large.jpg", 8.5, "2026-06-02 09:00:00", "uuid_cover_large.jpg")
        self._insert_material_record("video-large.mp4", 9.5, "2026-06-03 09:00:00", "uuid_video_large.mp4")

        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.get(
                "/getFiles?page=1&page_size=10&keyword=cover&material_type=图片&sort_by=filesize&sort_order=desc",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["pagination"]["total"], 2)
        self.assertEqual(
            [item["filename"] for item in payload["data"]],
            ["cover-large.jpg", "cover-small.jpg"],
        )

    def _prepare_database(self):
        """构造测试所需的最小数据库结构，避免依赖真实环境数据。"""
        db_dir = self.base_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(db_dir / "database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE file_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    filesize REAL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT,
                    remark TEXT DEFAULT ''
                )
                """
            )
            conn.commit()

    def _insert_material_record(self, filename, filesize, upload_time, file_path, remark=""):
        """向测试数据库写入素材记录，便于稳定校验分页与排序行为。"""
        with sqlite3.connect(self.base_dir / "db" / "database.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO file_records (filename, filesize, upload_time, file_path, remark)
                VALUES (?, ?, ?, ?, ?)
                """,
                (filename, filesize, upload_time, file_path, remark),
            )
            conn.commit()


if __name__ == "__main__":
    unittest.main()
