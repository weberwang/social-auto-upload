import subprocess
import sys
import unittest
from pathlib import Path


class CheckBackendDependenciesScriptTests(unittest.TestCase):
    """验证后端依赖预检脚本可直接通过脚本路径运行。"""

    def test_script_runs_without_module_import_error(self):
        """直接运行脚本时，应输出预检结果，而不是因找不到项目包崩溃。"""

        project_root = Path(__file__).resolve().parents[1]
        script_path = project_root / "scripts" / "check_backend_dependencies.py"

        completed = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        output = f"{completed.stdout}{completed.stderr}"

        self.assertIn(completed.returncode, (0, 1))
        self.assertNotIn("ModuleNotFoundError: No module named 'myUtils'", output)
        self.assertTrue(
            output.strip().startswith(("OK", "MISSING:")),
            msg=f"unexpected output: {output!r}",
        )


if __name__ == "__main__":
    unittest.main()
