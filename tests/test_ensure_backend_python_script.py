import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "win32", "仅在 Windows 上验证启动脚本")
class EnsureBackendPythonScriptTests(unittest.TestCase):
    """验证后端 Python 预检脚本在安装命令输出警告时仍能成功收敛。"""

    def test_start_win_batch_is_ascii_only(self):
        """Windows cmd 对非 ASCII 注释较脆弱，启动批处理应保持 ASCII 编码内容。"""

        project_root = Path(__file__).resolve().parents[1]
        batch_path = project_root / "start-win.bat"

        batch_bytes = batch_path.read_bytes()

        self.assertFalse(
            any(byte > 127 for byte in batch_bytes),
            msg="start-win.bat contains non-ASCII bytes and may exit early under cmd.exe",
        )

    def test_script_writes_env_file_when_installer_warns_on_stderr(self):
        """安装命令即使向 stderr 输出 warning，只要退出成功也应写出环境变量文件。"""

        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "scripts" / "ensure-backend-python.ps1"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            state_file = temp_path / "installed.flag"
            dependency_check_script = temp_path / "check_backend_dependencies.py"
            fake_python = temp_path / "fake-python.bat"
            env_output_file = temp_path / "python-env.cmd"

            dependency_check_script.write_text("# placeholder\n", encoding="utf-8")
            fake_python.write_text(
                textwrap.dedent(
                    f"""\
                    @echo off
                    setlocal
                    if /I "%~1"=="{dependency_check_script}" (
                        if exist "{state_file}" (
                            echo OK
                            exit /b 0
                        )
                        echo MISSING:click
                        exit /b 1
                    )
                    if /I "%~1"=="-m" if /I "%~2"=="pip" if /I "%~3"=="install" (
                        >"{state_file}" echo installed
                        >&2 echo warning: fake installer emitted stderr output
                        exit /b 0
                    )
                    >&2 echo unexpected args: %*
                    exit /b 2
                    """
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script_path),
                    "-VenvPythonExe",
                    str(fake_python),
                    "-PyprojectFile",
                    str(temp_path / "missing-pyproject.toml"),
                    "-UvLockFile",
                    str(temp_path / "missing-uv.lock"),
                    "-RequirementsFile",
                    str(project_root / "requirements.txt"),
                    "-DependencyCheckScript",
                    str(dependency_check_script),
                    "-EnvOutputFile",
                    str(env_output_file),
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, msg=completed.stderr)
            self.assertTrue(env_output_file.exists(), msg=completed.stderr)
            env_output = env_output_file.read_text(encoding="utf-8")
            self.assertIn(f'set "PYTHON_EXE={fake_python}"', env_output)
            self.assertIn('set "PYTHON_SOURCE=.venv"', env_output)
            self.assertIn(
                "warning: fake installer emitted stderr output",
                completed.stderr,
            )


if __name__ == "__main__":
    unittest.main()
