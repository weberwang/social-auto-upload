import unittest
from unittest.mock import patch

from myUtils.backend_runtime import find_missing_backend_modules


class BackendRuntimeTests(unittest.TestCase):
    """验证后端运行时依赖探测逻辑。"""

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
