from __future__ import annotations

import json
import subprocess
import sys
import unittest


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


if __name__ == "__main__":
    unittest.main()
