from __future__ import annotations

import json
import time
from typing import Any

from flask import Flask, Response, jsonify, request, stream_with_context


def _encode_sse(event_type: str, payload: dict[str, Any]) -> str:
    """把结构化事件编码成标准 SSE 文本帧。"""

    return f"event: {event_type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _get_queue_size(services: dict[str, Any]) -> int:
    """从当前注入的服务中读取队列规模，保持健康检查响应稳定。"""

    task_queue = services["task_queue"]
    return task_queue.size()


def register_mcp_routes(app: Flask, services: dict[str, Any]) -> None:
    """把 `/mcp` 基础路由注册到 Flask 应用。"""

    def _json_error(message: str, status_code: int = 400) -> tuple[Any, int]:
        """统一返回可被客户端消费的 JSON 错误，避免路由层抛 500。"""

        return jsonify({"error": message}), status_code

    @app.get("/mcp/health")
    def mcp_health() -> Any:
        """返回 MCP 服务的最小健康检查信息。"""

        return jsonify(
            {
                "status": "ok",
                "service": "social-auto-upload-mcp",
                "queue_size": _get_queue_size(services),
            }
        )

    @app.get("/mcp/capabilities")
    def mcp_capabilities() -> Any:
        """返回客户端需要先探测的工具与平台能力矩阵。"""

        capability_service = services["capability_service"]
        return jsonify(capability_service.get_capabilities())

    @app.post("/mcp/tasks")
    def mcp_create_task() -> Any:
        """把底层工具请求转成交给 dispatcher 的统一任务创建接口。"""

        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not payload:
            return _json_error("request body must be a non-empty JSON object")

        if "tool" not in payload:
            return _json_error("tool is required")

        tool_name = str(payload["tool"])
        input_payload = payload.get("input")
        if not isinstance(input_payload, dict):
            return _json_error("input must be an object")

        task_dispatcher = services["task_dispatcher"]
        try:
            result = task_dispatcher.submit_tool(tool_name, input_payload)
        except ValueError as exc:
            return _json_error(str(exc))
        return jsonify(result), 202

    @app.get("/mcp/tasks/<task_id>/events")
    def mcp_task_events(task_id: str) -> Response | tuple[Any, int]:
        """把任务历史事件按 SSE 形式输出，供前端实时消费。"""

        repository = services["repository"]
        try:
            repository.get_task(task_id)
        except KeyError:
            return _json_error("task not found", 404)

        def generate() -> Any:
            """按顺序把仓储里的事件逐条转成 SSE 帧。"""

            seen = 0
            terminal_statuses = {"succeeded", "failed", "cancelled"}
            terminal_seen_once = False
            while True:
                events = repository.list_events(task_id)
                while seen < len(events):
                    event = events[seen]
                    seen += 1
                    yield _encode_sse(
                        event.event_type,
                        {
                            "task_id": event.task_id,
                            "event_type": event.event_type,
                            "status": event.status,
                            "message": event.message,
                            "timestamp": event.timestamp,
                            "data": event.data,
                        },
                    )
                current_status = repository.get_task(task_id).status
                if current_status in terminal_statuses:
                    if seen >= len(events) and terminal_seen_once:
                        break
                    terminal_seen_once = seen >= len(events)
                else:
                    terminal_seen_once = False
                time.sleep(0.05)

        response = Response(stream_with_context(generate()), mimetype="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        return response
