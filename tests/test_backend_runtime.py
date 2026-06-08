import unittest
from unittest.mock import patch
from pathlib import Path
import re

from myUtils.backend_runtime import REQUIRED_BACKEND_MODULES, find_missing_backend_modules


class BackendRuntimeTests(unittest.TestCase):
    """验证后端运行时依赖探测逻辑。"""

    def _read_requirements_text(self) -> str:
        """兼容仓库里现有的 Windows UTF-16 编码，以及后续可能切回的 UTF-8。"""

        requirements_path = Path("requirements.txt")
        for encoding in ("utf-8-sig", "utf-16", "utf-16-le"):
            try:
                return requirements_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        msg = "requirements.txt 编码无法识别"
        raise AssertionError(msg)

    def test_required_backend_modules_cover_backend_startup_imports(self):
        """预检模块集合至少要覆盖后端启动阶段会立即导入的第三方依赖。"""

        self.assertTrue(
            {"segno", "playwright", "patchright", "xhs", "loguru", "cv2"}.issubset(REQUIRED_BACKEND_MODULES),
        )

    def test_required_backend_modules_are_installable_from_requirements(self):
        """预检要求的关键模块应能从 Windows 启动脚本使用的 requirements.txt 安装到。"""

        requirements_text = self._read_requirements_text()
        requirement_names = {
            re.split(r"[<>=!~]+", line, maxsplit=1)[0].strip().lower()
            for line in requirements_text.splitlines()
            if line.strip()
        }
        module_to_requirement_name = {
            "flask": "flask[async]",
            "flask_cors": "flask-cors",
            "jinja2": "jinja2",
            "itsdangerous": "itsdangerous",
            "werkzeug": "werkzeug",
            "click": "click",
            "blinker": "blinker",
            "segno": "segno",
            "playwright": "playwright",
            "patchright": "patchright",
            "xhs": "xhs",
            "loguru": "loguru",
            "cv2": "opencv-python",
        }

        missing_requirements = [
            module_name
            for module_name in REQUIRED_BACKEND_MODULES
            if module_to_requirement_name[module_name].lower() not in requirement_names
        ]

        self.assertEqual(missing_requirements, [])

    def test_find_missing_backend_modules_returns_missing_names_in_order(self):
        """缺失模块应按输入顺序返回，便于启动脚本输出稳定诊断信息。"""

        def fake_find_spec(module_name):
            if module_name in {"click", "flask_cors"}:
                return None
            return object()

        with patch("myUtils.backend_runtime.find_spec", side_effect=fake_find_spec):
            result = find_missing_backend_modules(
                ["flask", "click", "flask_cors", "werkzeug"],
            )

        self.assertEqual(result, ["click", "flask_cors"])


if __name__ == "__main__":
    unittest.main()
