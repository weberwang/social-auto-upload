from __future__ import annotations

import os

from flask import Flask

from sau_mcp_server.http.routes import register_mcp_routes
from sau_mcp_server.queue.task_queue import TaskQueue
from sau_mcp_server.repositories.task_repository import InMemoryTaskRepository
from sau_mcp_server.services.account_service import AccountService
from sau_mcp_server.services.capability_service import CapabilityService
from sau_mcp_server.services.platform_service import PlatformService
from sau_mcp_server.tools.dispatcher import ToolDispatcher


def create_mcp_app() -> Flask:
    """创建独立的 MCP Flask 应用，便于测试和后续独立启动。"""

    app = Flask(__name__)
    repository = InMemoryTaskRepository()
    task_queue = TaskQueue(repository=repository)
    platform_service = PlatformService()
    task_dispatcher = ToolDispatcher(task_queue=task_queue, platform_service=platform_service)
    account_service = AccountService()
    capability_service = CapabilityService(account_service=account_service)
    services = {
        "repository": repository,
        "task_queue": task_queue,
        "task_dispatcher": task_dispatcher,
        "platform_service": platform_service,
        "account_service": account_service,
        "capability_service": capability_service,
    }
    app.extensions["mcp_services"] = services
    register_mcp_routes(app, services)
    return app


def main() -> None:
    """提供 `sau-mcp` 命令入口，直接启动 MCP HTTP 服务。"""

    app = create_mcp_app()
    port = int(os.environ.get("SAU_MCP_PORT", "5410"))
    app.run(host=os.environ.get("SAU_MCP_HOST", "127.0.0.1"), port=port)
