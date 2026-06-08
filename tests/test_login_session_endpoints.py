import importlib
import sys
import threading
import types
import unittest
from queue import Queue
from pathlib import Path

for module_name in (
    "myUtils.auth",
    "uploader.douyin_uploader.main",
    "uploader.tencent_uploader.main",
    "playwright.async_api",
    "utils.base_social_media",
    "utils.log",
):
    sys.modules.pop(module_name, None)

conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
conf_stub.DEBUG_MODE = True
conf_stub.XHS_SERVER = "http://127.0.0.1:11901"
sys.modules["conf"] = conf_stub

sau_backend = importlib.import_module("sau_backend")

from sau_backend import (
    _cleanup_login_session,
    _get_login_session,
    _register_login_session,
    app,
    sse_stream,
)


class LoginSessionEndpointTests(unittest.TestCase):
    """验证登录会话的取消与终态关闭行为。"""

    def setUp(self):
        """为每个用例准备独立测试客户端。"""

        self.client = app.test_client()

    def tearDown(self):
        """兜底清理可能残留的测试会话。"""

        _cleanup_login_session("test-session")
        _cleanup_login_session("stream-session")

    def test_cancel_login_endpoint_marks_session_cancelled_and_enqueues_terminal(self):
        """取消接口应设置取消信号，并向 SSE 队列推送取消终态。"""

        queue = Queue()
        cancel_event = threading.Event()
        _register_login_session("test-session", "2", "creator", queue, cancel_event)

        response = self.client.post("/login/cancel", json={"session_id": "test-session"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["code"], 200)
        self.assertTrue(cancel_event.is_set())
        self.assertEqual(queue.get_nowait(), "LOG:登录会话:cancel_requested:会话已取消，session_id=test-session")
        self.assertEqual(queue.get_nowait(), "CANCELLED")

    def test_sse_stream_breaks_after_terminal_and_cleans_session(self):
        """SSE 流收到终态消息后应停止迭代，并清理会话注册表。"""

        queue = Queue()
        cancel_event = threading.Event()
        _register_login_session("stream-session", "2", "creator", queue, cancel_event)
        queue.put("SESSION:stream-session")
        queue.put("CANCELLED")

        stream_messages = list(sse_stream(queue, cancel_event, "stream-session"))

        self.assertEqual(
            stream_messages,
            ["data: SESSION:stream-session\n\n", "data: CANCELLED\n\n"],
        )
        self.assertIsNone(_get_login_session("stream-session"))


if __name__ == "__main__":
    unittest.main()
