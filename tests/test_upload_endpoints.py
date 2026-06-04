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
        """`/uploadSave` 需要同时完成文件保存和数据库记录写入。"""
        with patch("sau_backend.BASE_DIR", self.base_dir):
            response = self.client.post(
                "/uploadSave",
                data={
                    "file": (BytesIO(b"video-bytes"), "sample.mp4"),
                    "filename": "renamed-video",
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
                "SELECT filename, file_path FROM file_records WHERE file_path = ?",
                (payload["data"]["filepath"],),
            )
            record = cursor.fetchone()

        self.assertEqual(record, ("renamed-video.mp4", payload["data"]["filepath"]))

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
                    file_path TEXT
                )
                """
            )
            conn.commit()


if __name__ == "__main__":
    unittest.main()
