from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

import sau_mcp_launcher


class SauMcpLauncherTests(unittest.TestCase):
    """验证 `sau-mcp` 启动 shim 会把 host/port 透传给 Node 服务。"""

    def test_launcher_passes_host_and_port_to_node(self):
        with patch("sau_mcp_launcher.subprocess.run") as mock_run:
            os.environ["SAU_MCP_HOST"] = "127.0.0.1"
            os.environ["SAU_MCP_PORT"] = "5410"
            sau_mcp_launcher.main()

        args = mock_run.call_args.args[0]
        self.assertEqual(args[0], "node")
        self.assertIn("5410", args)
        self.assertIn("127.0.0.1", args)
        self.assertTrue(args[1].endswith(str(Path("sau_mcp_node") / "dist" / "src" / "cli.js")))


if __name__ == "__main__":
    unittest.main()
