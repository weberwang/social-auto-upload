from __future__ import annotations

from sau_cli_account_helpers import _require_safe_account_name
from sau_mcp_server.models.task import TaskRecord
from sau_mcp_server.services.models import PlatformCheckRequest, PlatformLoginRequest
from sau_mcp_server.services.platform_service import PlatformService


def _require_non_empty_string(field_name: str, value: object) -> str:
    """校验必填文本字段，避免把列表、空值等隐式转换成字符串后继续入队。"""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


class ToolDispatcher:
    """把 MCP 工具名转换成统一任务记录，供 HTTP 层调用。"""

    def __init__(self, task_queue, platform_service: PlatformService) -> None:
        """保存队列与平台服务引用，便于后续扩展更多工具。"""

        self.task_queue = task_queue
        self.platform_service = platform_service

    def submit_tool(self, tool_name: str, payload: dict[str, object]) -> dict[str, object]:
        """把底层工具请求转换成任务记录，并返回任务受理信息。"""

        if tool_name not in {"platform_login", "platform_check"}:
            raise ValueError(f"Unsupported tool: {tool_name}")

        if not isinstance(payload, dict):
            raise ValueError("input must be an object")

        if "platform" not in payload or "account_name" not in payload:
            raise ValueError("platform_login requires platform and account_name")

        platform = _require_non_empty_string("platform", payload["platform"])
        account_name = _require_safe_account_name(payload["account_name"])
        if tool_name == "platform_login":
            headless = payload.get("headless", True)
            if "headless" in payload and not isinstance(headless, bool):
                raise ValueError("headless must be a boolean")

            task = TaskRecord.create(
                task_type="platform_login",
                platform=platform,
                account_name=account_name,
                input_payload={
                    "platform": platform,
                    "account_name": account_name,
                    "headless": headless,
                },
            )

            async def _run_login() -> dict[str, object]:
                """登录任务只做参数转换，真正执行交给共享平台 service。"""

                result = await self.platform_service.login(
                    PlatformLoginRequest(platform=platform, account_name=account_name, headless=headless)
                )
                if isinstance(result, dict) and result.get("success") is False:
                    raise ValueError(result.get("message") or "platform login failed")
                return result

            message = "平台登录任务已创建"
            data = {"tool": tool_name}
            self.task_queue.enqueue_task(task, message=message, data=data)
            self.task_queue.submit_background(task, _run_login)
            return {"task_id": task.task_id, "status": task.status}

        task = TaskRecord.create(
            task_type="platform_check",
            platform=platform,
            account_name=account_name,
            input_payload={
                "platform": platform,
                "account_name": account_name,
            },
        )

        async def _run_check() -> dict[str, object]:
            """校验任务复用同一套平台 service，不再在路由层重复实现。"""

            is_valid = await self.platform_service.check(
                PlatformCheckRequest(platform=platform, account_name=account_name)
            )
            return {"valid": is_valid}

        self.task_queue.enqueue_task(task, message="平台校验任务已创建", data={"tool": tool_name})
        self.task_queue.submit_background(task, _run_check)
        return {"task_id": task.task_id, "status": task.status}
