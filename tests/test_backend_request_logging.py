import unittest
from unittest.mock import patch

import sau_backend


class BackendRequestLoggingTests(unittest.TestCase):
    """验证后端会为每个请求输出统一访问日志。"""

    def setUp(self):
        """创建测试客户端，用于触发 Flask 请求流程。"""
        self.client = sau_backend.app.test_client()

    def test_request_logging_prints_method_path_status_and_duration(self):
        """请求结束后，应输出包含方法、路径、状态码和耗时的日志。"""
        probe_path = "/__codex_request_log_probe__"

        with patch("builtins.print") as mock_print:
            response = self.client.get(probe_path)

        self.assertEqual(response.status_code, 404)
        printed_messages = [call.args[0] for call in mock_print.call_args_list if call.args]
        self.assertTrue(
            any(
                message.startswith(f"[REQ] GET {probe_path} -> 404")
                and message.endswith("ms")
                for message in printed_messages
            ),
            f"expected request log for {probe_path}, got: {printed_messages}",
        )


if __name__ == "__main__":
    unittest.main()
