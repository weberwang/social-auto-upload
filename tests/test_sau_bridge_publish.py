from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import unittest
from unittest.mock import AsyncMock, patch

from sau_bridge.publish import run_publish_note


class SauBridgePublishTests(unittest.TestCase):
    """验证发布 bridge 在失败路径上也只输出标准 JSON。"""

    def test_publish_video_outputs_json_error_for_unsupported_platform(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sau_bridge",
                "publish-video",
                "--json-input",
                json.dumps(
                    {
                        "platform": "unknown",
                        "account_name": "creator",
                        "file_path": "demo.mp4",
                        "title": "标题",
                    },
                    ensure_ascii=False,
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["success"], False)
        self.assertEqual(payload["error"]["code"], "bridge_execution_failed")

    def test_run_publish_note_parses_tencent_platform_fields(self):
        payload = {
            "platform": "tencent",
            "account_name": "creator",
            "image_files": ["1.png", "2.png"],
            "title": "图文标题",
            "note": "图文正文",
            "tags": ["旅行"],
            "collection_name": "旅行合集",
            "declare_original": True,
            "original_type": "生活",
            "content_declaration": "无需声明",
            "is_draft": True,
        }

        with patch("sau_cli.upload_tencent_note", new=AsyncMock(return_value="cookies/tencent_creator.json")) as mock_upload:
            result = asyncio.run(run_publish_note(payload))

        self.assertTrue(result["success"])
        request = mock_upload.await_args.args[0]
        self.assertEqual(request.collection_name, "旅行合集")
        self.assertTrue(request.declare_original)
        self.assertEqual(request.original_type, "生活")
        self.assertEqual(request.content_declaration, "无需声明")
        self.assertTrue(request.is_draft)


if __name__ == "__main__":
    unittest.main()
