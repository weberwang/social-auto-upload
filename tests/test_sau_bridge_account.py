from __future__ import annotations

import json
import subprocess
import sys
import unittest


class SauBridgeAccountTests(unittest.TestCase):
    """验证账号 bridge 的 stdout 协议保持机器可读。"""

    def test_account_check_outputs_json_only(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "sau_bridge",
                "account-check",
                "--json-input",
                json.dumps({"platform": "douyin", "account_name": "missing-demo"}, ensure_ascii=False),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["success"], True)
        self.assertEqual(payload["data"], {"valid": False})


if __name__ == "__main__":
    unittest.main()
