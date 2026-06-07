from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> None:
    """保留 `sau-mcp` 命令名不变，并把启动入口切到 Node MCP 服务。"""

    project_root = Path(__file__).resolve().parent
    node_entry = project_root / "sau_mcp_node" / "dist" / "src" / "cli.js"
    command = [
        "node",
        str(node_entry),
        "--host",
        os.environ.get("SAU_MCP_HOST", "127.0.0.1"),
        "--port",
        os.environ.get("SAU_MCP_PORT", "5410"),
    ]
    subprocess.run(command, check=True, cwd=project_root)


if __name__ == "__main__":
    main()
