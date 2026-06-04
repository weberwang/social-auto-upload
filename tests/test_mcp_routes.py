import asyncio
import time
import unittest
from unittest.mock import AsyncMock, patch

from sau_mcp_server.app import create_mcp_app


class McpRouteTests(unittest.TestCase):
    """验证 MCP HTTP 接口的最小可用性。"""

    def setUp(self) -> None:
        """为每个测试创建独立的 Flask 测试客户端。"""

        self.client = create_mcp_app().test_client()

    def test_health_returns_service_metadata(self) -> None:
        """健康检查必须返回基础服务元信息，便于客户端先确认存活。"""

        response = self.client.get("/mcp/health")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "social-auto-upload-mcp")
        self.assertIn("queue_size", payload)

    def test_capabilities_include_low_level_tools_and_platforms(self) -> None:
        """能力接口必须先暴露工具与平台清单，供客户端做能力探测。"""

        response = self.client.get("/mcp/capabilities")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["tools"], ["platform_login", "platform_check"])
        self.assertEqual(
            payload["platforms"],
            ["douyin", "kuaishou", "xiaohongshu", "bilibili"],
        )


class McpTaskCreationTests(unittest.TestCase):
    """验证统一任务入口会把工具请求转成同步受理任务。"""

    def setUp(self) -> None:
        """为每个测试创建独立的 Flask 测试客户端。"""

        self.client = create_mcp_app().test_client()

    def test_create_login_task_eventually_completes(self) -> None:
        """创建平台登录任务后，后台执行必须把状态推进到终态。"""

        async def delayed_login(account_name: str, headless: bool = True) -> dict[str, object]:
            """用短延迟模拟真实平台登录，避免测试依赖外部网络。"""

            await asyncio.sleep(0.1)
            return {
                "success": True,
                "account_file": f"cookies/douyin_{account_name}.json",
                "headless": headless,
            }

        with patch(
            "sau_mcp_server.services.platform_adapters.login_douyin_account",
            new=AsyncMock(side_effect=delayed_login),
        ):
            response = self.client.post(
                "/mcp/tasks",
                json={
                    "tool": "platform_login",
                    "input": {
                        "platform": "douyin",
                        "account_name": "creator",
                        "headless": True,
                    },
                },
            )

            self.assertEqual(response.status_code, 202)
            payload = response.get_json()
            self.assertIsInstance(payload, dict)
            self.assertEqual(payload["status"], "queued")
            self.assertIn("task_id", payload)

            services = self.client.application.extensions["mcp_services"]
            repository = services["repository"]
            task_id = payload["task_id"]

            task = repository.get_task(task_id)
            self.assertEqual(task.task_type, "platform_login")
            self.assertEqual(
                task.input_payload,
                {"platform": "douyin", "account_name": "creator", "headless": True},
            )

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                stored_events = repository.list_events(task_id)
                if (
                    repository.get_task(task_id).status in {"succeeded", "failed"}
                    and stored_events
                    and stored_events[-1].event_type in {"task.succeeded", "task.failed"}
                ):
                    break
                time.sleep(0.02)

            stored = repository.get_task(task_id)
            self.assertEqual(stored.status, "succeeded")
            self.assertEqual(stored.result["success"], True)
            self.assertEqual(
                [event.event_type for event in repository.list_events(task_id)],
                ["task.queued", "task.running", "task.succeeded"],
            )

    def test_create_check_task_eventually_completes(self) -> None:
        """平台校验任务也必须真正进入后台执行流程。"""

        with patch(
            "sau_mcp_server.services.platform_adapters.check_douyin_account",
            new=AsyncMock(return_value=True),
        ):
            response = self.client.post(
                "/mcp/tasks",
                json={
                    "tool": "platform_check",
                    "input": {
                        "platform": "douyin",
                        "account_name": "creator",
                    },
                },
            )

            self.assertEqual(response.status_code, 202)
            payload = response.get_json()
            self.assertIsInstance(payload, dict)
            self.assertEqual(payload["status"], "queued")

            services = self.client.application.extensions["mcp_services"]
            repository = services["repository"]
            task_id = payload["task_id"]

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                stored_events = repository.list_events(task_id)
                if (
                    repository.get_task(task_id).status in {"succeeded", "failed"}
                    and stored_events
                    and stored_events[-1].event_type in {"task.succeeded", "task.failed"}
                ):
                    break
                time.sleep(0.02)

            stored = repository.get_task(task_id)
            self.assertEqual(stored.status, "succeeded")
            self.assertEqual(stored.result, {"valid": True})

    def test_create_login_task_marks_failed_when_login_returns_false(self) -> None:
        """登录协程返回 success=False 时，任务必须落到 failed。"""

        with patch(
            "sau_mcp_server.services.platform_adapters.login_douyin_account",
            new=AsyncMock(return_value={"success": False, "message": "login rejected"}),
        ):
            response = self.client.post(
                "/mcp/tasks",
                json={
                    "tool": "platform_login",
                    "input": {
                        "platform": "douyin",
                        "account_name": "creator",
                        "headless": True,
                    },
                },
            )

            self.assertEqual(response.status_code, 202)
            payload = response.get_json()
            self.assertIsInstance(payload, dict)
            task_id = payload["task_id"]

            services = self.client.application.extensions["mcp_services"]
            repository = services["repository"]

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                stored_events = repository.list_events(task_id)
                if (
                    repository.get_task(task_id).status in {"succeeded", "failed"}
                    and stored_events
                    and stored_events[-1].event_type in {"task.succeeded", "task.failed"}
                ):
                    break
                time.sleep(0.02)

            stored = repository.get_task(task_id)
            self.assertEqual(stored.status, "failed")
            self.assertIsNotNone(stored.error)
            self.assertEqual(stored.error["message"], "login rejected")
            self.assertEqual(
                [event.event_type for event in repository.list_events(task_id)],
                ["task.queued", "task.running", "task.failed"],
            )

    def test_task_events_stream_waits_for_terminal_events(self) -> None:
        """事件流必须持续等待，直到任务进入终态后才结束响应。"""

        async def delayed_login(account_name: str, headless: bool = True) -> dict[str, object]:
            """模拟稍慢的登录流程，确保 SSE 能观察到中间状态。"""

            await asyncio.sleep(0.1)
            return {
                "success": True,
                "account_file": f"cookies/douyin_{account_name}.json",
                "headless": headless,
            }

        with patch(
            "sau_mcp_server.services.platform_adapters.login_douyin_account",
            new=AsyncMock(side_effect=delayed_login),
        ):
            create_response = self.client.post(
                "/mcp/tasks",
                json={
                    "tool": "platform_login",
                    "input": {
                        "platform": "douyin",
                        "account_name": "creator",
                        "headless": True,
                    },
                },
            )

            task_id = create_response.get_json()["task_id"]

            response = self.client.get(f"/mcp/tasks/{task_id}/events")

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.headers["Content-Type"].startswith("text/event-stream"))
            body = response.get_data(as_text=True)
            self.assertIn("event: task.queued", body)
            self.assertIn("event: task.running", body)
            self.assertIn("event: task.succeeded", body)
            self.assertIn(f'"task_id": "{task_id}"', body)

    def test_create_task_rejects_empty_request_body(self) -> None:
        """空请求体应返回稳定的 JSON 4xx 错误。"""

        response = self.client.post("/mcp/tasks", data="", content_type="application/json")

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_task_rejects_unknown_tool(self) -> None:
        """不支持的工具名应返回稳定的 JSON 4xx 错误。"""

        response = self.client.post(
            "/mcp/tasks",
            json={
                "tool": "unknown",
                "input": {},
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_login_task_requires_platform_and_account_name(self) -> None:
        """platform_login 缺少必要字段时应返回稳定的 JSON 4xx 错误。"""

        response = self.client.post(
            "/mcp/tasks",
            json={
                "tool": "platform_login",
                "input": {},
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_login_task_rejects_non_string_platform(self) -> None:
        """platform 传入非字符串时必须直接拒绝，避免被隐式转成字符串。"""

        response = self.client.post(
            "/mcp/tasks",
            json={
                "tool": "platform_login",
                "input": {
                    "platform": None,
                    "account_name": "creator",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_login_task_rejects_non_boolean_headless(self) -> None:
        """headless 只能接受布尔值，字符串不能再被当成真值入队。"""

        response = self.client.post(
            "/mcp/tasks",
            json={
                "tool": "platform_login",
                "input": {
                    "platform": "douyin",
                    "account_name": "creator",
                    "headless": "false",
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_login_task_rejects_non_string_account_name(self) -> None:
        """account_name 传入容器类型时必须直接拒绝，防止错误账号进入队列。"""

        response = self.client.post(
            "/mcp/tasks",
            json={
                "tool": "platform_login",
                "input": {
                    "platform": "douyin",
                    "account_name": ["x"],
                },
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIsInstance(payload, dict)
        self.assertIn("error", payload)

    def test_create_login_task_rejects_path_traversal_account_names(self) -> None:
        """account_name 只允许安全字符，不能把路径分隔符带进任务队列。"""

        for account_name in ("../evil", "a/b", "a\\b"):
            with self.subTest(account_name=account_name):
                response = self.client.post(
                    "/mcp/tasks",
                    json={
                        "tool": "platform_login",
                        "input": {
                            "platform": "douyin",
                            "account_name": account_name,
                        },
                    },
                )

                self.assertEqual(response.status_code, 400)
                payload = response.get_json()
                self.assertIsInstance(payload, dict)
                self.assertIn("error", payload)
