import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "win32", "仅在 Windows 上验证前端启动脚本")
class StartFrontendDevScriptTests(unittest.TestCase):
    """验证前端启动脚本在后端未就绪时不会继续启动 Vite。"""

    def test_script_stops_before_running_npm_when_backend_wait_fails(self):
        """后端等待失败时，应直接退出，避免前端先启动后产生代理拒绝连接噪音。"""

        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "scripts" / "start-frontend-dev.ps1"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            frontend_dir = temp_path / "frontend"
            frontend_dir.mkdir()

            wait_script = temp_path / "wait-port.ps1"
            npm_bat = temp_path / "npm.bat"
            marker_file = temp_path / "npm-invoked.txt"

            # 用立即失败的假等待脚本稳定复现“后端未就绪”分支，避免测试真的等待 30 秒。
            wait_script.write_text("exit 1\n", encoding="utf-8")
            npm_bat.write_text(
                textwrap.dedent(
                    f"""\
                    @echo off
                    >"{marker_file}" echo invoked
                    exit /b 0
                    """
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PATH"] = f"{temp_path}{os.pathsep}{env['PATH']}"

            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script_path),
                    "-FrontendDir",
                    str(frontend_dir),
                    "-WaitPortScript",
                    str(wait_script),
                    "-BackendPort",
                    "5409",
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )

            self.assertNotEqual(completed.returncode, 0, msg=completed.stdout)
            self.assertFalse(
                marker_file.exists(),
                msg="backend wait failed but npm run dev was still invoked",
            )


if __name__ == "__main__":
    unittest.main()
