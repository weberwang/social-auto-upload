# MCP HTTP/SSE Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `social-auto-upload` 增加一套基于 `HTTP + SSE` 的 MCP Server，并让 CLI 与 MCP 共享一套平台 service 层。

**Architecture:** 先从 `sau_cli.py` 中抽出共享 request model 与平台 service，再建立任务模型、内存队列、SSE 事件流与 `/mcp` 路由，最后接入底层工具与高层发布任务。历史 `sau_backend.py` 保留旧接口，但通过独立模块注册 MCP 路由，避免继续把协议逻辑堆回旧文件。

**Tech Stack:** Python 3.10+, Flask, asyncio, unittest, dataclasses, queue/threading（仅保留旧接口兼容），现有 uploader/runtime 模块

---

## 文件结构

### 新增文件

- `sau_mcp_server/__init__.py`
  - MCP 服务包入口
- `sau_mcp_server/config.py`
  - MCP 服务配置读取与默认值
- `sau_mcp_server/models/task.py`
  - 任务状态、事件、任务实体定义
- `sau_mcp_server/repositories/task_repository.py`
  - 内存任务仓储与事件历史缓存
- `sau_mcp_server/queue/task_queue.py`
  - 异步任务队列、worker、取消逻辑
- `sau_mcp_server/http/sse.py`
  - SSE 编码与心跳输出
- `sau_mcp_server/http/routes.py`
  - `/mcp` 路由注册
- `sau_mcp_server/tools/dispatcher.py`
  - `tool + input` 任务分发器
- `sau_mcp_server/services/models.py`
  - 共享 request model
- `sau_mcp_server/services/platform_service.py`
  - 登录、校验、上传统一 service
- `sau_mcp_server/services/account_service.py`
  - 账号读取 service
- `sau_mcp_server/services/capability_service.py`
  - 平台能力矩阵 service
- `sau_mcp_server/app.py`
  - MCP Flask app factory 与启动入口
- `tests/test_platform_service.py`
  - 平台 service 测试
- `tests/test_mcp_task_queue.py`
  - 任务模型与队列测试
- `tests/test_mcp_routes.py`
  - `/mcp` HTTP/SSE 接口测试

### 修改文件

- `sau_cli.py`
  - 改为薄入口，调用共享 service，不继续堆业务逻辑
- `sau_backend.py`
  - 注册独立 MCP 路由，不把 MCP 逻辑直接写进主文件
- `pyproject.toml`
  - 把 `sau_mcp_server*` 加入打包范围，并增加服务启动脚本
- `README.md`
  - 增加 MCP Server 使用说明
- `docs/CLI.md`
  - 增加 `sau mcp serve` 或独立脚本启动说明

### 责任边界

- `services/*` 负责共享业务能力，CLI 与 MCP 都可调用
- `models/repositories/queue/*` 负责任务编排，不关心 HTTP 或 CLI
- `http/*` 负责协议输出，不直接触碰 uploader 细节
- `tools/dispatcher.py` 负责将外部 `tool` 名称映射到 service 调用

## Task 1: 抽共享 request model 与平台 service

**Files:**
- Create: `sau_mcp_server/services/models.py`
- Create: `sau_mcp_server/services/platform_service.py`
- Test: `tests/test_platform_service.py`
- Modify: `sau_cli.py`

- [ ] **Step 1: 写失败测试，锁定平台 service 的最小行为**

```python
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from sau_mcp_server.services.models import PlatformLoginRequest
from sau_mcp_server.services.platform_service import PlatformService


class PlatformServiceTests(unittest.TestCase):
    """验证共享平台 service 会把请求分发到现有主线能力。"""

    def test_login_dispatches_douyin_request(self):
        service = PlatformService()
        request = PlatformLoginRequest(platform="douyin", account_name="creator", headless=True)

        with patch(
            "sau_mcp_server.services.platform_service.login_douyin_account",
            new=AsyncMock(return_value={"success": True, "account_file": "cookies/douyin_creator.json"}),
        ) as mock_login:
            result = asyncio.run(service.login(request))

        mock_login.assert_awaited_once_with("creator", headless=True)
        self.assertTrue(result["success"])
```

- [ ] **Step 2: 运行测试，确认因为模块未创建而失败**

Run: `rtk python -m unittest tests.test_platform_service.PlatformServiceTests.test_login_dispatches_douyin_request -v`
Expected: `FAILED (errors=1)`，并提示 `ModuleNotFoundError: No module named 'sau_mcp_server'`

- [ ] **Step 3: 写最小 request model 与平台 service 实现**

```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class PlatformLoginRequest:
    """描述一次平台登录任务。"""

    platform: str
    account_name: str
    headless: bool = True


@dataclass(slots=True)
class PlatformCheckRequest:
    """描述一次账号状态校验任务。"""

    platform: str
    account_name: str


@dataclass(slots=True)
class UploadVideoRequest:
    """描述一次视频上传任务。"""

    platform: str
    account_name: str
    file: Path
    title: str
    desc: str
    tags: list[str]
    schedule: datetime | int
    extra: dict[str, object] | None = None
```

```python
from sau_cli import (
    check_bilibili_account,
    check_douyin_account,
    check_kuaishou_account,
    check_xiaohongshu_account,
    login_bilibili_account,
    login_douyin_account,
    login_kuaishou_account,
    login_xiaohongshu_account,
)


class PlatformService:
    """封装 CLI 与 MCP 共享的平台主线能力。"""

    async def login(self, request):
        if request.platform == "douyin":
            return await login_douyin_account(request.account_name, headless=request.headless)
        if request.platform == "kuaishou":
            return await login_kuaishou_account(request.account_name, headless=request.headless)
        if request.platform == "xiaohongshu":
            return await login_xiaohongshu_account(request.account_name, headless=request.headless)
        if request.platform == "bilibili":
            return await login_bilibili_account(request.account_name)
        raise ValueError(f"Unsupported platform: {request.platform}")

    async def check(self, request):
        if request.platform == "douyin":
            return await check_douyin_account(request.account_name)
        if request.platform == "kuaishou":
            return await check_kuaishou_account(request.account_name)
        if request.platform == "xiaohongshu":
            return await check_xiaohongshu_account(request.account_name)
        if request.platform == "bilibili":
            return await check_bilibili_account(request.account_name)
        raise ValueError(f"Unsupported platform: {request.platform}")
```

- [ ] **Step 4: 再跑测试，确认 service 分发已通过**

Run: `rtk python -m unittest tests.test_platform_service.PlatformServiceTests.test_login_dispatches_douyin_request -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_server/services/models.py sau_mcp_server/services/platform_service.py tests/test_platform_service.py
git commit -m "feat: extract shared platform service"
```

## Task 2: 收缩 `sau_cli.py`，改为薄入口并接入共享 service

**Files:**
- Modify: `sau_cli.py`
- Modify: `tests/test_sau_browser_cli.py`
- Test: `tests/test_sau_bilibili_cli.py`

- [ ] **Step 1: 写失败测试，锁定 CLI 会通过共享 service 处理登录**

```python
import asyncio
import unittest
from argparse import Namespace
from unittest.mock import AsyncMock, patch

import sau_cli


class SauCliServiceIntegrationTests(unittest.TestCase):
    """验证 CLI 入口不会重新实现平台业务逻辑。"""

    def test_dispatch_login_uses_platform_service(self):
        args = Namespace(platform="douyin", action="login", account="creator", headless=True)

        with patch("sau_cli.platform_service.login", new=AsyncMock(return_value={"success": True, "account_file": "x"})) as mock_login:
            code = asyncio.run(sau_cli.dispatch(args))

        self.assertEqual(code, 0)
        mock_login.assert_awaited_once()
```

- [ ] **Step 2: 运行测试，确认现有 `dispatch` 还没有接入共享 service**

Run: `rtk python -m unittest tests.test_sau_browser_cli.SauCliServiceIntegrationTests.test_dispatch_login_uses_platform_service -v`
Expected: `FAILED`，并提示 `AttributeError` 或断言 `Expected mock to have been awaited once. Awaited 0 times.`

- [ ] **Step 3: 在 `sau_cli.py` 中改成薄入口，避免继续增长大文件**

```python
from sau_mcp_server.services.models import PlatformCheckRequest, PlatformLoginRequest
from sau_mcp_server.services.platform_service import PlatformService


platform_service = PlatformService()


async def dispatch(args: argparse.Namespace) -> int:
    if args.platform == "douyin" and args.action == "login":
        result = await platform_service.login(
            PlatformLoginRequest(platform="douyin", account_name=args.account, headless=args.headless)
        )
        if not result["success"]:
            raise RuntimeError(result["message"])
        print(f"Douyin login flow completed: {result['account_file']}")
        return 0

    if args.platform == "douyin" and args.action == "check":
        is_valid = await platform_service.check(
            PlatformCheckRequest(platform="douyin", account_name=args.account)
        )
        print("valid" if is_valid else "invalid")
        return 0 if is_valid else 1
```

- [ ] **Step 4: 运行 CLI 相关测试，确认行为没回归**

Run: `rtk python -m unittest tests.test_sau_browser_cli tests.test_sau_bilibili_cli -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_cli.py tests/test_sau_browser_cli.py tests/test_sau_bilibili_cli.py
git commit -m "refactor: route cli through shared platform service"
```

## Task 3: 建立任务模型、内存仓储与异步队列

**Files:**
- Create: `sau_mcp_server/models/task.py`
- Create: `sau_mcp_server/repositories/task_repository.py`
- Create: `sau_mcp_server/queue/task_queue.py`
- Test: `tests/test_mcp_task_queue.py`

- [ ] **Step 1: 写失败测试，锁定任务入队后会流转到成功状态**

```python
import asyncio
import unittest

from sau_mcp_server.models.task import TaskRecord
from sau_mcp_server.queue.task_queue import TaskQueue
from sau_mcp_server.repositories.task_repository import InMemoryTaskRepository


class McpTaskQueueTests(unittest.TestCase):
    """验证 MCP 任务队列会正确更新状态并记录事件。"""

    def test_submit_runs_job_and_marks_task_succeeded(self):
        repository = InMemoryTaskRepository()
        queue = TaskQueue(repository=repository)

        async def sample_job():
            return {"ok": True}

        task = TaskRecord.create(task_type="platform.check", platform="douyin", account_name="creator", input_payload={})
        asyncio.run(queue.submit(task, sample_job))

        stored = repository.get_task(task.task_id)
        self.assertEqual(stored.status, "succeeded")
        self.assertEqual(stored.result, {"ok": True})
```

- [ ] **Step 2: 运行测试，确认因为任务模块缺失而失败**

Run: `rtk python -m unittest tests.test_mcp_task_queue.McpTaskQueueTests.test_submit_runs_job_and_marks_task_succeeded -v`
Expected: `FAILED (errors=1)`，并提示 `ModuleNotFoundError`

- [ ] **Step 3: 写最小任务实体、仓储与队列实现**

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class TaskEvent:
    """描述任务生命周期中的一次事件。"""

    event: str
    task_id: str
    status: str
    message: str
    timestamp: str
    data: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class TaskRecord:
    """描述一条 MCP 异步任务记录。"""

    task_id: str
    task_type: str
    platform: str | None
    account_name: str | None
    status: str
    input_payload: dict[str, object]
    result: dict[str, object] | None = None
    error: dict[str, object] | None = None

    @classmethod
    def create(cls, task_type: str, platform: str | None, account_name: str | None, input_payload: dict[str, object]):
        return cls(
            task_id=f"task_{uuid4().hex}",
            task_type=task_type,
            platform=platform,
            account_name=account_name,
            status="queued",
            input_payload=input_payload,
        )
```

```python
class InMemoryTaskRepository:
    """以内存保存任务与事件，便于第一版快速落地。"""

    def __init__(self):
        self._tasks = {}
        self._events = {}

    def save_task(self, task):
        self._tasks[task.task_id] = task
        self._events.setdefault(task.task_id, [])

    def get_task(self, task_id):
        return self._tasks[task_id]

    def append_event(self, event):
        self._events.setdefault(event.task_id, []).append(event)
```

```python
class TaskQueue:
    """顺序执行第一版 MCP 任务，并把结果回写到仓储。"""

    def __init__(self, repository):
        self.repository = repository

    async def submit(self, task, job_factory):
        self.repository.save_task(task)
        task.status = "running"
        result = await job_factory()
        task.status = "succeeded"
        task.result = result
        self.repository.save_task(task)
        return task
```

- [ ] **Step 4: 运行队列测试，确认状态流转通过**

Run: `rtk python -m unittest tests.test_mcp_task_queue -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_server/models/task.py sau_mcp_server/repositories/task_repository.py sau_mcp_server/queue/task_queue.py tests/test_mcp_task_queue.py
git commit -m "feat: add mcp task model and queue"
```

## Task 4: 建立 SSE 编码与 `/mcp` 基础路由

**Files:**
- Create: `sau_mcp_server/http/sse.py`
- Create: `sau_mcp_server/http/routes.py`
- Create: `sau_mcp_server/app.py`
- Test: `tests/test_mcp_routes.py`
- Modify: `sau_backend.py`

- [ ] **Step 1: 写失败测试，锁定 `/mcp/health` 与 `/mcp/tasks` 的最小接口**

```python
import unittest

from sau_mcp_server.app import create_mcp_app


class McpRouteTests(unittest.TestCase):
    """验证 MCP HTTP 接口的最小可用性。"""

    def setUp(self):
        self.client = create_mcp_app().test_client()

    def test_health_returns_service_metadata(self):
        response = self.client.get("/mcp/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("queue_size", payload)
```

- [ ] **Step 2: 运行测试，确认 MCP app 与路由尚不存在**

Run: `rtk python -m unittest tests.test_mcp_routes.McpRouteTests.test_health_returns_service_metadata -v`
Expected: `FAILED (errors=1)`，并提示 `ModuleNotFoundError` 或 `ImportError`

- [ ] **Step 3: 写最小 app factory、SSE 编码器与基础路由**

```python
import json


def encode_sse(event_name: str, payload: dict[str, object]) -> str:
    """把结构化事件编码为标准 SSE 文本帧。"""

    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
```

```python
from flask import Flask, jsonify


def register_mcp_routes(app: Flask, services: dict[str, object]) -> None:
    @app.get("/mcp/health")
    def mcp_health():
        queue = services["task_queue"]
        return jsonify({"status": "ok", "queue_size": queue.size(), "service": "social-auto-upload-mcp"})
```

```python
from flask import Flask

from sau_mcp_server.http.routes import register_mcp_routes
from sau_mcp_server.queue.task_queue import TaskQueue
from sau_mcp_server.repositories.task_repository import InMemoryTaskRepository


def create_mcp_app() -> Flask:
    app = Flask(__name__)
    repository = InMemoryTaskRepository()
    queue = TaskQueue(repository=repository)
    register_mcp_routes(app, {"repository": repository, "task_queue": queue})
    return app
```

- [ ] **Step 4: 运行 MCP 路由测试，确认基础路由通过**

Run: `rtk python -m unittest tests.test_mcp_routes -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_server/http/sse.py sau_mcp_server/http/routes.py sau_mcp_server/app.py sau_backend.py tests/test_mcp_routes.py
git commit -m "feat: add mcp app and base routes"
```

## Task 5: 接入底层工具分发与任务创建接口

**Files:**
- Create: `sau_mcp_server/tools/dispatcher.py`
- Modify: `sau_mcp_server/http/routes.py`
- Modify: `sau_mcp_server/services/platform_service.py`
- Modify: `tests/test_mcp_routes.py`

- [ ] **Step 1: 写失败测试，锁定 `POST /mcp/tasks` 会创建 `platform_login` 任务**

```python
import unittest
from unittest.mock import AsyncMock, patch

from sau_mcp_server.app import create_mcp_app


class McpTaskCreationTests(unittest.TestCase):
    """验证统一任务入口会把工具请求转成异步任务。"""

    def setUp(self):
        self.client = create_mcp_app().test_client()

    def test_create_login_task_returns_task_id(self):
        with patch("sau_mcp_server.http.routes.task_dispatcher.submit_tool", new=AsyncMock(return_value={"task_id": "task_demo", "status": "queued"})):
            response = self.client.post(
                "/mcp/tasks",
                json={"tool": "platform_login", "input": {"platform": "douyin", "account_name": "creator", "headless": True}},
            )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["task_id"], "task_demo")
```

- [ ] **Step 2: 运行测试，确认统一任务入口尚未实现**

Run: `rtk python -m unittest tests.test_mcp_routes.McpTaskCreationTests.test_create_login_task_returns_task_id -v`
Expected: `FAILED`，并提示 `404 != 202`

- [ ] **Step 3: 写工具分发器与统一任务创建实现**

```python
from sau_mcp_server.models.task import TaskRecord
from sau_mcp_server.services.models import PlatformLoginRequest


class ToolDispatcher:
    """把 MCP 工具请求转成任务与 service 调用。"""

    def __init__(self, task_queue, platform_service):
        self.task_queue = task_queue
        self.platform_service = platform_service

    async def submit_tool(self, tool_name: str, payload: dict[str, object]):
        if tool_name == "platform_login":
            task = TaskRecord.create(
                task_type="platform.login",
                platform=str(payload["platform"]),
                account_name=str(payload["account_name"]),
                input_payload=payload,
            )

            async def run_job():
                request = PlatformLoginRequest(
                    platform=str(payload["platform"]),
                    account_name=str(payload["account_name"]),
                    headless=bool(payload.get("headless", True)),
                )
                return await self.platform_service.login(request)

            await self.task_queue.submit(task, run_job)
            return {"task_id": task.task_id, "status": task.status}

        raise ValueError(f"Unsupported tool: {tool_name}")
```

```python
@app.post("/mcp/tasks")
def create_task():
    payload = request.get_json() or {}
    result = asyncio.run(task_dispatcher.submit_tool(payload["tool"], payload.get("input", {})))
    return jsonify(result), 202
```

- [ ] **Step 4: 运行 MCP 任务创建测试，确认底层工具已接通**

Run: `rtk python -m unittest tests.test_mcp_routes.McpTaskCreationTests.test_create_login_task_returns_task_id -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_server/tools/dispatcher.py sau_mcp_server/http/routes.py sau_mcp_server/services/platform_service.py tests/test_mcp_routes.py
git commit -m "feat: add mcp task creation for low-level tools"
```

## Task 6: 接入高层能力、SSE 事件流、打包与文档

**Files:**
- Create: `sau_mcp_server/services/account_service.py`
- Create: `sau_mcp_server/services/capability_service.py`
- Modify: `sau_mcp_server/http/routes.py`
- Modify: `sau_mcp_server/queue/task_queue.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/CLI.md`
- Modify: `tests/test_mcp_routes.py`

- [ ] **Step 1: 写失败测试，锁定 `/mcp/capabilities` 和任务事件流**

```python
import unittest

from sau_mcp_server.app import create_mcp_app


class McpCapabilityTests(unittest.TestCase):
    """验证客户端可先读取能力矩阵，再发起执行任务。"""

    def setUp(self):
        self.client = create_mcp_app().test_client()

    def test_capabilities_include_low_and_high_level_tools(self):
        response = self.client.get("/mcp/capabilities")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("platform_login", payload["tools"])
        self.assertIn("create_publish_task", payload["tools"])
```

- [ ] **Step 2: 运行测试，确认能力接口与事件接口尚未完善**

Run: `rtk python -m unittest tests.test_mcp_routes.McpCapabilityTests.test_capabilities_include_low_and_high_level_tools -v`
Expected: `FAILED`，并提示 `404 != 200`

- [ ] **Step 3: 实现能力 service、账号 service、SSE 事件接口与打包入口**

```python
class CapabilityService:
    """集中维护 MCP 对外暴露的工具与平台能力矩阵。"""

    def get_capabilities(self) -> dict[str, object]:
        return {
            "tools": [
                "platform_login",
                "platform_check",
                "upload_video",
                "upload_note",
                "create_publish_task",
                "cancel_task",
            ],
            "platforms": ["douyin", "kuaishou", "xiaohongshu", "bilibili"],
        }
```

```python
@app.get("/mcp/capabilities")
def mcp_capabilities():
    return jsonify(capability_service.get_capabilities())


@app.get("/mcp/tasks/<task_id>/events")
def stream_task_events(task_id: str):
    def generate():
        for event in repository.list_events(task_id):
            yield encode_sse(event.event, {"task_id": event.task_id, "status": event.status, "message": event.message, "data": event.data})

    return Response(generate(), mimetype="text/event-stream")
```

```toml
[project.scripts]
sau = "sau_cli:main"
sau-mcp = "sau_mcp_server.app:main"

[tool.setuptools.packages.find]
include = ["uploader*", "utils*", "myUtils*", "sau_mcp_server*"]
```

```markdown
## MCP Server

启动 MCP 服务：

```bash
sau-mcp
```

健康检查：

```bash
curl http://127.0.0.1:5409/mcp/health
```
```

- [ ] **Step 4: 运行完整 MCP 测试，确认能力接口、事件流与打包入口都已通过**

Run: `rtk python -m unittest tests.test_mcp_routes tests.test_mcp_task_queue tests.test_platform_service -v`
Expected: `OK`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_server/services/account_service.py sau_mcp_server/services/capability_service.py sau_mcp_server/http/routes.py sau_mcp_server/queue/task_queue.py pyproject.toml README.md docs/CLI.md tests/test_mcp_routes.py
git commit -m "feat: complete mcp server capabilities and docs"
```

## Self-Review

- **Spec coverage:** 已覆盖共享 service、异步任务队列、SSE 事件、统一任务入口、底层工具、高层能力矩阵、打包入口与文档更新。未覆盖分布式队列与非主线平台，符合 spec 非目标定义。
- **Placeholder scan:** 计划中没有 `TBD`、`TODO`、`类似 Task N`、`自行补全` 之类占位描述；每个代码步骤都给出了最小代码骨架和精确命令。
- **Type consistency:** 统一使用 `PlatformLoginRequest`、`TaskRecord`、`InMemoryTaskRepository`、`TaskQueue`、`ToolDispatcher` 这些固定名字；后续执行时应保持这些命名不再漂移。
