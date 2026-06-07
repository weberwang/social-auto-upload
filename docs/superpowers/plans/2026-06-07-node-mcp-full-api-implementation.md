# Node MCP 全量 API 补全实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `social-auto-upload` 的 MCP 服务层迁移到 Node.js，并补齐主线平台的账号、发布、草稿、定时计划、任务与 SSE 事件能力，同时保持本地运行行为不变。

**Architecture:** 在仓库根部新增独立的 `sau_mcp_node/` Node 服务，负责 HTTP、SSE、任务编排、SQLite 持久化与调度；保留 Python 平台执行层，通过新增 `sau_bridge` JSON 子进程桥接 Node 与现有 `helper/uploader/biliup`。`sau-mcp` 命令不改名，通过 Python 启动 shim 接管到 Node 服务。

**Tech Stack:** Node.js 20+, TypeScript, Fastify, better-sqlite3, Zod, Vitest, Python 3.10+, unittest, 现有 uploader/runtime 模块

---

## 文件结构

### 新增文件

- `sau_mcp_node/package.json`
  - Node MCP 独立包定义，使用 `npm`，不和 `sau_frontend` 混用依赖
- `sau_mcp_node/tsconfig.json`
  - TypeScript 编译配置
- `sau_mcp_node/vitest.config.ts`
  - Node MCP 测试配置
- `sau_mcp_node/src/cli.ts`
  - Node MCP 启动入口，读取 host/port 并启动服务
- `sau_mcp_node/src/app.ts`
  - Fastify app 装配
- `sau_mcp_node/src/config.ts`
  - 环境变量读取与默认值
- `sau_mcp_node/src/shared/platforms.ts`
  - 平台字符串、旧平台编号、内容类型、能力矩阵统一映射
- `sau_mcp_node/src/shared/errors.ts`
  - 统一业务错误与 HTTP 错误映射
- `sau_mcp_node/src/domain/task.ts`
  - 父任务实体与状态规则
- `sau_mcp_node/src/domain/child-task.ts`
  - 子任务实体与状态规则
- `sau_mcp_node/src/domain/schedule.ts`
  - 定时计划实体与状态规则
- `sau_mcp_node/src/db/schema.ts`
  - SQLite 建表 SQL
- `sau_mcp_node/src/db/migrator.ts`
  - SQLite 初始化与迁移执行器
- `sau_mcp_node/src/db/connection.ts`
  - `better-sqlite3` 连接与事务包装
- `sau_mcp_node/src/repositories/task-repository.ts`
  - 父任务仓储
- `sau_mcp_node/src/repositories/child-task-repository.ts`
  - 子任务仓储
- `sau_mcp_node/src/repositories/task-event-repository.ts`
  - 事件仓储
- `sau_mcp_node/src/repositories/draft-repository.ts`
  - MCP 草稿仓储与旧草稿导入逻辑
- `sau_mcp_node/src/repositories/schedule-repository.ts`
  - 定时计划仓储
- `sau_mcp_node/src/repositories/account-snapshot-repository.ts`
  - 账号快照仓储
- `sau_mcp_node/src/bridges/python-runner.ts`
  - Python 子进程执行器
- `sau_mcp_node/src/bridges/python-account-bridge.ts`
  - 账号登录/校验桥接
- `sau_mcp_node/src/bridges/python-publish-bridge.ts`
  - 视频/图文发布桥接
- `sau_mcp_node/src/validators/account.ts`
  - 账号类输入校验
- `sau_mcp_node/src/validators/publish.ts`
  - 发布类输入校验
- `sau_mcp_node/src/services/capability-service.ts`
  - 能力矩阵服务，包含 `tencent`
- `sau_mcp_node/src/services/account-service.ts`
  - 本地账号枚举与快照聚合
- `sau_mcp_node/src/services/draft-service.ts`
  - 草稿保存、读取、删除、兼容导入
- `sau_mcp_node/src/services/task-service.ts`
  - 任务列表、详情、子任务列表、事件读取
- `sau_mcp_node/src/services/schedule-service.ts`
  - 计划 CRUD 与状态查询
- `sau_mcp_node/src/executors/account-executor.ts`
  - 账号任务执行器
- `sau_mcp_node/src/executors/publish-executor.ts`
  - 父子发布任务执行器
- `sau_mcp_node/src/executors/task-control-executor.ts`
  - 取消与重试执行器
- `sau_mcp_node/src/scheduler/schedule-runner.ts`
  - 服务内调度器与计划恢复
- `sau_mcp_node/src/http/routes/health.ts`
  - `/mcp/health`
- `sau_mcp_node/src/http/routes/capabilities.ts`
  - `/mcp/capabilities`
- `sau_mcp_node/src/http/routes/accounts.ts`
  - `/mcp/accounts`
- `sau_mcp_node/src/http/routes/drafts.ts`
  - `/mcp/drafts*`
- `sau_mcp_node/src/http/routes/tasks.ts`
  - `/mcp/tasks*`
- `sau_mcp_node/src/http/routes/task-events.ts`
  - 任务 SSE 路由
- `sau_mcp_node/src/http/routes/schedules.ts`
  - `/mcp/schedules*`
- `sau_mcp_node/src/http/routes/tools.ts`
  - `/mcp/tools/:tool_name` 与旧 `/mcp/tasks` dispatch
- `sau_mcp_node/tests/contracts/mcp-compat.spec.ts`
  - 锁定旧 MCP 协议兼容
- `sau_mcp_node/tests/contracts/draft-compat.spec.ts`
  - 锁定旧草稿兼容策略
- `sau_mcp_node/tests/unit/python-runner.spec.ts`
  - Python runner 成功/失败/编码/超时测试
- `sau_mcp_node/tests/unit/platform-mapping.spec.ts`
  - 平台映射与能力矩阵测试
- `sau_mcp_node/tests/integration/task-flow.spec.ts`
  - 父子任务执行流测试
- `sau_mcp_node/tests/integration/schedule-runner.spec.ts`
  - 调度与重启恢复测试
- `sau_mcp_node/tests/integration/sse-events.spec.ts`
  - SSE 重放与终态收尾测试
- `sau_bridge/__init__.py`
  - Python bridge 包入口
- `sau_bridge/__main__.py`
  - `python -m sau_bridge` 命令入口
- `sau_bridge/cli.py`
  - bridge 子命令解析
- `sau_bridge/account.py`
  - 账号 bridge 实现
- `sau_bridge/publish.py`
  - 发布 bridge 实现
- `tests/test_sau_bridge_account.py`
  - Python bridge 账号测试
- `tests/test_sau_bridge_publish.py`
  - Python bridge 发布测试
- `sau_mcp_launcher.py`
  - 保留 `sau-mcp` 命令名的 Python 启动 shim

### 修改文件

- `pyproject.toml`
  - 增加 `sau_bridge*` 打包范围，并将 `sau-mcp` 入口改到 `sau_mcp_launcher:main`
- `README.md`
  - 更新 Node MCP 启动与工具清单
- `docs/CLI.md`
  - 更新 Node MCP 说明、工具契约和调试命令
- `requirements.txt`
  - 如 Python bridge 需要新增标准依赖，则在此同步

### 责任边界

- `sau_mcp_node/src/http/*` 只处理协议，不直接碰 uploader 细节
- `sau_mcp_node/src/executors/*` 只负责任务推进，不直接读写 HTTP
- `sau_mcp_node/src/bridges/*` 只负责 Node -> Python JSON 协议
- `sau_bridge/*` 只负责 Python 内部复用现有 helper/uploader，不再重复实现 CLI 逻辑
- `sau_mcp_launcher.py` 只做 Node 进程启动与环境透传，不承载业务

## 先锁定的实施决策

- Node MCP 独立放在 `sau_mcp_node/`，不复用 `sau_frontend` 工程。
- Node 包管理器固定为 `npm`，保持与仓库现有 `package-lock.json` 习惯一致。
- `sau-mcp` 命令保持不变，通过 `sau_mcp_launcher.py` 启动 `node sau_mcp_node/dist/cli.js`。
- `tencent` 必须纳入新的 `capabilities`、账号、发布工具面。
- 旧草稿表 `publish_drafts` 做一次性导入到 `mcp_publish_drafts`，导入后 Node MCP 只读写新表。
- 服务端延迟调度与平台内定时发布不叠加：`schedule_create` 只负责“延迟启动任务”；子任务执行时统一按立即发布处理，避免双重定时语义冲突。
- 图文多图按“一组图片 = 一个素材单元 = 一个子任务”处理，不拆成单图子任务。
- 父任务部分成功统一记为 `failed`，但 `result_payload.summary` 必须包含 `success_count`、`failed_count`、`cancelled_count`。
- `running` 任务在服务重启后统一标记为 `failed`，错误码固定为 `service_restarted_during_execution`。

## Task 1: 初始化 Node MCP 工程与兼容契约基线

**Files:**
- Create: `sau_mcp_node/package.json`
- Create: `sau_mcp_node/tsconfig.json`
- Create: `sau_mcp_node/vitest.config.ts`
- Create: `sau_mcp_node/src/shared/platforms.ts`
- Create: `sau_mcp_node/tests/contracts/mcp-compat.spec.ts`
- Create: `sau_mcp_node/tests/unit/platform-mapping.spec.ts`

- [ ] **Step 1: 写失败测试，先锁旧 MCP 协议和新增 Tencent 能力矩阵**

```ts
import { describe, expect, it } from "vitest";
import { buildCapabilityMatrix, LEGACY_PLATFORM_ID_MAP } from "../../src/shared/platforms";

describe("capability matrix", () => {
  it("keeps old platform order and appends tencent in the new matrix", () => {
    const matrix = buildCapabilityMatrix();
    expect(matrix.legacyPlatforms).toEqual(["douyin", "kuaishou", "xiaohongshu", "bilibili"]);
    expect(matrix.platforms).toEqual(["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"]);
    expect(matrix.platformDetails.tencent.supportedMaterialTypes).toEqual(["video", "image_text"]);
    expect(LEGACY_PLATFORM_ID_MAP[5]).toBe("bilibili");
  });
});
```

- [ ] **Step 2: 运行测试，确认 Node 工程尚未建立**

Run: `cd sau_mcp_node && npm test -- tests/unit/platform-mapping.spec.ts`
Expected: `The system cannot find the path specified` 或 `npm ERR! enoent`

- [ ] **Step 3: 建立最小 Node 工程骨架与平台映射文件**

```json
{
  "name": "sau-mcp-node",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "vitest run"
  },
  "dependencies": {
    "better-sqlite3": "^11.10.0",
    "fastify": "^5.0.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/node": "^22.10.2",
    "typescript": "^5.8.3",
    "vitest": "^2.1.8"
  }
}
```

```ts
export const LEGACY_PLATFORM_ID_MAP: Record<number, string> = {
  1: "xiaohongshu",
  2: "tencent",
  3: "douyin",
  4: "kuaishou",
  5: "bilibili",
};
```

- [ ] **Step 4: 再跑测试，确认平台矩阵约束通过**

Run: `cd sau_mcp_node && npm test -- tests/unit/platform-mapping.spec.ts`
Expected: `1 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_node/package.json sau_mcp_node/tsconfig.json sau_mcp_node/vitest.config.ts sau_mcp_node/src/shared/platforms.ts sau_mcp_node/tests/contracts/mcp-compat.spec.ts sau_mcp_node/tests/unit/platform-mapping.spec.ts
git commit -m "feat: scaffold node mcp package"
```

## Task 2: 建 SQLite 模式、迁移器和旧草稿导入

**Files:**
- Create: `sau_mcp_node/src/db/schema.ts`
- Create: `sau_mcp_node/src/db/connection.ts`
- Create: `sau_mcp_node/src/db/migrator.ts`
- Create: `sau_mcp_node/src/repositories/draft-repository.ts`
- Create: `sau_mcp_node/tests/contracts/draft-compat.spec.ts`
- Create: `sau_mcp_node/tests/integration/sqlite-migrator.spec.ts`

- [ ] **Step 1: 写失败测试，锁定旧 `publish_drafts` 可导入到新草稿表**

```ts
import { describe, expect, it } from "vitest";

describe("draft migration", () => {
  it("imports legacy publish_drafts rows into mcp_publish_drafts", async () => {
    const result = await importLegacyDrafts();
    expect(result.importedCount).toBe(1);
  });
});
```

- [ ] **Step 2: 写失败测试，锁定新表和计划表会在初始化时创建**

```ts
import { describe, expect, it } from "vitest";

describe("migrator", () => {
  it("creates task, child task, event, draft, schedule and account snapshot tables", async () => {
    const tables = await listTables();
    expect(tables).toContain("mcp_tasks");
    expect(tables).toContain("mcp_publish_drafts");
    expect(tables).toContain("mcp_schedules");
  });
});
```

- [ ] **Step 3: 实现 schema 与 migrator，并固定旧草稿导入策略**

```ts
export const CREATE_TABLE_STATEMENTS = [
  `CREATE TABLE IF NOT EXISTS mcp_tasks (...);`,
  `CREATE TABLE IF NOT EXISTS mcp_task_children (...);`,
  `CREATE TABLE IF NOT EXISTS mcp_task_events (...);`,
  `CREATE TABLE IF NOT EXISTS mcp_publish_drafts (...);`,
  `CREATE TABLE IF NOT EXISTS mcp_schedules (...);`,
  `CREATE TABLE IF NOT EXISTS mcp_accounts_snapshot (...);`,
];
```

```ts
// 只导入旧表一次，导入后新 MCP 只读写 mcp_publish_drafts。
db.prepare(`
  INSERT INTO mcp_publish_drafts (legacy_draft_id, name, workspace_payload, created_at, updated_at)
  SELECT id, name, payload, created_at, updated_at
  FROM publish_drafts
  WHERE id NOT IN (SELECT legacy_draft_id FROM mcp_publish_drafts WHERE legacy_draft_id IS NOT NULL)
`).run();
```

- [ ] **Step 4: 运行数据库测试，确认表和导入逻辑通过**

Run: `cd sau_mcp_node && npm test -- tests/contracts/draft-compat.spec.ts tests/integration/sqlite-migrator.spec.ts`
Expected: `2 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_node/src/db/schema.ts sau_mcp_node/src/db/connection.ts sau_mcp_node/src/db/migrator.ts sau_mcp_node/src/repositories/draft-repository.ts sau_mcp_node/tests/contracts/draft-compat.spec.ts sau_mcp_node/tests/integration/sqlite-migrator.spec.ts
git commit -m "feat: add sqlite schema and legacy draft import"
```

## Task 3: 建 Python bridge 协议与 Python 端子命令

**Files:**
- Create: `sau_bridge/__init__.py`
- Create: `sau_bridge/__main__.py`
- Create: `sau_bridge/cli.py`
- Create: `sau_bridge/account.py`
- Create: `sau_bridge/publish.py`
- Create: `tests/test_sau_bridge_account.py`
- Create: `tests/test_sau_bridge_publish.py`
- Create: `sau_mcp_node/src/bridges/python-runner.ts`
- Create: `sau_mcp_node/src/bridges/python-account-bridge.ts`
- Create: `sau_mcp_node/src/bridges/python-publish-bridge.ts`
- Create: `sau_mcp_node/tests/unit/python-runner.spec.ts`
- Modify: `pyproject.toml`

- [ ] **Step 1: 写 Python 失败测试，锁定 bridge stdout 只能输出 JSON**

```python
import json
import subprocess
import sys
import unittest


class SauBridgeAccountTests(unittest.TestCase):
    def test_account_check_outputs_json_only(self):
        result = subprocess.run(
            [sys.executable, "-m", "sau_bridge", "account-check", "--json-input", '{"platform":"douyin","account_name":"demo"}'],
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("success", payload)
```

- [ ] **Step 2: 写 Node 失败测试，锁定非零退出码和 stderr 会映射为 bridge 错误**

```ts
import { describe, expect, it } from "vitest";

describe("python runner", () => {
  it("throws bridge error when python exits non-zero", async () => {
    await expect(runPython(["-c", "import sys; sys.stderr.write('boom'); sys.exit(2)"])).rejects.toMatchObject({
      code: "python_bridge_failed",
    });
  });
});
```

- [ ] **Step 3: 实现 bridge CLI 和 Node runner，并锁定 JSON 协议**

```python
def _print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), end="")
```

```ts
export type PythonBridgeResult = {
  success: boolean;
  data?: Record<string, unknown>;
  error?: { code: string; message: string };
};
```

- [ ] **Step 4: 运行 Python 与 Node bridge 测试**

Run: `python -m unittest tests.test_sau_bridge_account tests.test_sau_bridge_publish -v`
Expected: `OK`

Run: `cd sau_mcp_node && npm test -- tests/unit/python-runner.spec.ts`
Expected: `1 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_bridge sau_mcp_node/src/bridges sau_mcp_node/tests/unit/python-runner.spec.ts tests/test_sau_bridge_account.py tests/test_sau_bridge_publish.py pyproject.toml
git commit -m "feat: add python bridge protocol"
```

## Task 4: 实现查询类与同步写接口

**Files:**
- Create: `sau_mcp_node/src/services/capability-service.ts`
- Create: `sau_mcp_node/src/services/account-service.ts`
- Create: `sau_mcp_node/src/services/draft-service.ts`
- Create: `sau_mcp_node/src/services/schedule-service.ts`
- Create: `sau_mcp_node/src/http/routes/health.ts`
- Create: `sau_mcp_node/src/http/routes/capabilities.ts`
- Create: `sau_mcp_node/src/http/routes/accounts.ts`
- Create: `sau_mcp_node/src/http/routes/drafts.ts`
- Create: `sau_mcp_node/src/http/routes/schedules.ts`
- Create: `sau_mcp_node/src/app.ts`
- Create: `sau_mcp_node/tests/contracts/query-routes.spec.ts`

- [ ] **Step 1: 写失败测试，锁定 `health/capabilities/accounts/drafts/schedules` 返回结构**

```ts
import { describe, expect, it } from "vitest";

describe("query routes", () => {
  it("returns health metadata and tencent in capabilities", async () => {
    const app = await buildApp();
    const health = await app.inject({ method: "GET", url: "/mcp/health" });
    const capabilities = await app.inject({ method: "GET", url: "/mcp/capabilities" });
    expect(health.json().service).toBe("social-auto-upload-mcp");
    expect(capabilities.json().platforms).toContain("tencent");
  });
});
```

- [ ] **Step 2: 实现最小 Fastify app 和查询路由**

```ts
app.get("/mcp/health", async () => ({
  status: "ok",
  service: "social-auto-upload-mcp",
  queue_size: 0,
}));
```

```ts
app.get("/mcp/capabilities", async () => capabilityService.getCapabilities());
app.get("/mcp/accounts", async () => accountService.listAccounts());
app.get("/mcp/drafts", async () => draftService.listDrafts());
app.get("/mcp/schedules", async () => scheduleService.listSchedules());
```

- [ ] **Step 3: 运行查询路由测试**

Run: `cd sau_mcp_node && npm test -- tests/contracts/query-routes.spec.ts`
Expected: `1 passed`

- [ ] **Step 4: 提交这一小步**

```bash
git add sau_mcp_node/src/services sau_mcp_node/src/http/routes sau_mcp_node/src/app.ts sau_mcp_node/tests/contracts/query-routes.spec.ts
git commit -m "feat: add node mcp query routes"
```

## Task 5: 实现父子任务仓储、旧 `/mcp/tasks` 兼容和 SSE

**Files:**
- Create: `sau_mcp_node/src/domain/task.ts`
- Create: `sau_mcp_node/src/domain/child-task.ts`
- Create: `sau_mcp_node/src/repositories/task-repository.ts`
- Create: `sau_mcp_node/src/repositories/child-task-repository.ts`
- Create: `sau_mcp_node/src/repositories/task-event-repository.ts`
- Create: `sau_mcp_node/src/services/task-service.ts`
- Create: `sau_mcp_node/src/http/routes/tasks.ts`
- Create: `sau_mcp_node/src/http/routes/task-events.ts`
- Create: `sau_mcp_node/src/http/routes/tools.ts`
- Create: `sau_mcp_node/tests/contracts/mcp-compat.spec.ts`
- Create: `sau_mcp_node/tests/integration/sse-events.spec.ts`

- [ ] **Step 1: 写失败测试，锁定旧 `/mcp/tasks` 兼容入口仍返回 `202 + queued`**

```ts
import { describe, expect, it } from "vitest";

describe("legacy task entry", () => {
  it("accepts platform_login style payload and returns queued task", async () => {
    const app = await buildApp();
    const response = await app.inject({
      method: "POST",
      url: "/mcp/tasks",
      payload: { tool: "platform_login", input: { platform: "douyin", account_name: "demo", headless: true } },
    });
    expect(response.statusCode).toBe(202);
    expect(response.json().status).toBe("queued");
  });
});
```

- [ ] **Step 2: 写失败测试，锁定 SSE 会先回放历史，再等终态**

```ts
import { describe, expect, it } from "vitest";

describe("task events", () => {
  it("replays queued/running/succeeded in order", async () => {
    const events = await collectTaskEvents("task_demo");
    expect(events.map((event) => event.event_type)).toEqual(["task.queued", "task.running", "task.succeeded"]);
  });
});
```

- [ ] **Step 3: 实现任务仓储、旧工具名映射与 SSE 事件读取**

```ts
const LEGACY_TOOL_ALIAS = {
  platform_login: "account_login",
  platform_check: "account_check",
} as const;
```

```ts
reply.raw.write(`event: ${event.event_type}\n`);
reply.raw.write(`data: ${JSON.stringify(event)}\n\n`);
```

- [ ] **Step 4: 运行兼容路由与 SSE 测试**

Run: `cd sau_mcp_node && npm test -- tests/contracts/mcp-compat.spec.ts tests/integration/sse-events.spec.ts`
Expected: `2 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_node/src/domain sau_mcp_node/src/repositories/task-repository.ts sau_mcp_node/src/repositories/child-task-repository.ts sau_mcp_node/src/repositories/task-event-repository.ts sau_mcp_node/src/services/task-service.ts sau_mcp_node/src/http/routes/tasks.ts sau_mcp_node/src/http/routes/task-events.ts sau_mcp_node/src/http/routes/tools.ts sau_mcp_node/tests/contracts/mcp-compat.spec.ts sau_mcp_node/tests/integration/sse-events.spec.ts
git commit -m "feat: add task repositories and sse routes"
```

## Task 6: 实现账号任务与发布任务展开执行

**Files:**
- Create: `sau_mcp_node/src/validators/account.ts`
- Create: `sau_mcp_node/src/validators/publish.ts`
- Create: `sau_mcp_node/src/executors/account-executor.ts`
- Create: `sau_mcp_node/src/executors/publish-executor.ts`
- Create: `sau_mcp_node/src/executors/task-control-executor.ts`
- Create: `sau_mcp_node/tests/integration/task-flow.spec.ts`

- [ ] **Step 1: 写失败测试，锁定 `publish_submit` 会按 `平台 x 账号 x 素材单元` 展开子任务**

```ts
import { describe, expect, it } from "vitest";

describe("publish submit", () => {
  it("creates one child task per platform-account-material unit", async () => {
    const result = await submitPublishTask({
      trigger_mode: "immediate",
      content_type: "image_text",
      targets: [
        { platform: "douyin", account_name: "a" },
        { platform: "kuaishou", account_name: "b" },
      ],
      materials: [{ type: "image_text", files: ["1.png", "2.png"] }],
      metadata: { title: "x", note: "y", tags: ["z"] },
    });
    expect(result.childCount).toBe(2);
  });
});
```

- [ ] **Step 2: 写失败测试，锁定同一 `platform + account_name` 串行**

```ts
import { describe, expect, it } from "vitest";

describe("publish executor", () => {
  it("does not run two child tasks for the same platform-account in parallel", async () => {
    const timeline = await runSerialConstraintScenario();
    expect(timeline.overlapDetected).toBe(false);
  });
});
```

- [ ] **Step 3: 实现输入校验、账号任务执行器和发布任务执行器**

```ts
export const accountLoginSchema = z.object({
  platform: z.enum(["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"]),
  account_name: z.string().regex(/^[A-Za-z0-9_-]+$/),
  headless: z.boolean().default(true),
});
```

```ts
// 图文多图是一组素材单元，不拆单图子任务。
const buildChildUnits = (payload: PublishPayload) => {
  return payload.targets.flatMap((target) =>
    payload.materials.map((material) => ({
      platform: target.platform,
      accountName: target.account_name,
      materialPayload: material,
    })),
  );
};
```

- [ ] **Step 4: 运行任务流测试**

Run: `cd sau_mcp_node && npm test -- tests/integration/task-flow.spec.ts`
Expected: `1 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_node/src/validators sau_mcp_node/src/executors sau_mcp_node/tests/integration/task-flow.spec.ts
git commit -m "feat: add account and publish executors"
```

## Task 7: 实现计划服务、调度器、防重复触发和重启恢复

**Files:**
- Create: `sau_mcp_node/src/domain/schedule.ts`
- Create: `sau_mcp_node/src/repositories/schedule-repository.ts`
- Create: `sau_mcp_node/src/scheduler/schedule-runner.ts`
- Create: `sau_mcp_node/tests/integration/schedule-runner.spec.ts`

- [ ] **Step 1: 写失败测试，锁定计划到点只触发一次父任务**

```ts
import { describe, expect, it } from "vitest";

describe("schedule runner", () => {
  it("claims one pending schedule and produces one publish task only once", async () => {
    const result = await runDueScheduleScenario();
    expect(result.triggeredTaskCount).toBe(1);
  });
});
```

- [ ] **Step 2: 写失败测试，锁定重启后 `running` 任务会标记失败**

```ts
import { describe, expect, it } from "vitest";

describe("restart recovery", () => {
  it("marks running tasks failed with service_restarted_during_execution", async () => {
    const task = await recoverAfterRestart();
    expect(task.status).toBe("failed");
    expect(task.error_payload.code).toBe("service_restarted_during_execution");
  });
});
```

- [ ] **Step 3: 实现计划抢锁和恢复规则**

```ts
UPDATE mcp_schedules
SET status = 'running', locked_at = ?, locked_by = ?
WHERE id = ? AND status = 'pending' AND locked_at IS NULL;
```

```ts
UPDATE mcp_tasks
SET status = 'failed', error_payload = ?
WHERE status = 'running';
```

- [ ] **Step 4: 运行调度测试**

Run: `cd sau_mcp_node && npm test -- tests/integration/schedule-runner.spec.ts`
Expected: `2 passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_node/src/domain/schedule.ts sau_mcp_node/src/repositories/schedule-repository.ts sau_mcp_node/src/scheduler/schedule-runner.ts sau_mcp_node/tests/integration/schedule-runner.spec.ts
git commit -m "feat: add schedule runner and recovery rules"
```

## Task 8: 切换 `sau-mcp` 入口并更新文档

**Files:**
- Create: `sau_mcp_launcher.py`
- Create: `tests/test_sau_mcp_launcher.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/CLI.md`

- [ ] **Step 1: 写失败测试，锁定 `sau-mcp` 启动 shim 会把端口透传给 Node**

```python
import os
import unittest
from unittest.mock import patch

import sau_mcp_launcher


class SauMcpLauncherTests(unittest.TestCase):
    def test_launcher_passes_host_and_port_to_node(self):
        with patch("sau_mcp_launcher.subprocess.run") as mock_run:
            os.environ["SAU_MCP_PORT"] = "5410"
            sau_mcp_launcher.main()
        args = mock_run.call_args.args[0]
        self.assertIn("node", args[0].lower())
        self.assertIn("5410", " ".join(args))
```

- [ ] **Step 2: 实现最小启动 shim，并把 `pyproject.toml` 改到新入口**

```python
def main() -> None:
    node_entry = Path(__file__).resolve().parent / "sau_mcp_node" / "dist" / "cli.js"
    command = ["node", str(node_entry), "--host", os.environ.get("SAU_MCP_HOST", "127.0.0.1"), "--port", os.environ.get("SAU_MCP_PORT", "5410")]
    subprocess.run(command, check=True)
```

- [ ] **Step 3: 更新文档，明确新工具清单和兼容入口**

```md
- `POST /mcp/tools/account_login`
- `POST /mcp/tools/account_check`
- `POST /mcp/tools/publish_submit`
- `POST /mcp/tools/task_retry`
- `POST /mcp/tools/task_cancel`
- `POST /mcp/tasks`（旧客户端兼容入口）
```

- [ ] **Step 4: 运行 Python 启动测试与 Node 全量测试**

Run: `python -m unittest tests.test_sau_bridge_account tests.test_sau_bridge_publish tests.test_sau_mcp_launcher -v`
Expected: `OK`

Run: `cd sau_mcp_node && npm test`
Expected: `all tests passed`

- [ ] **Step 5: 提交这一小步**

```bash
git add sau_mcp_launcher.py pyproject.toml README.md docs/CLI.md tests/test_sau_mcp_launcher.py
git commit -m "feat: switch sau-mcp entrypoint to node service"
```

## 最终验证波次

- [ ] **Step 1: 跑 Node MCP 契约测试，确认旧协议兼容行为未丢**

Run: `cd sau_mcp_node && npm test -- tests/contracts/mcp-compat.spec.ts tests/contracts/query-routes.spec.ts tests/integration/sse-events.spec.ts`
Expected: `all tests passed`，并确认以下兼容行为已锁定：

- `GET /mcp/health` 仍返回 `service=social-auto-upload-mcp`
- `POST /mcp/tasks` 仍接受旧 `tool + input` 结构
- SSE 事件顺序仍为 `queued -> running -> terminal`

- [ ] **Step 2: 跑旧草稿接口测试，确认旧数据可导入**

Run: `python -m unittest tests.test_publish_draft_endpoints -v`
Expected: 旧后端草稿接口继续可用；Node MCP 导入逻辑不破坏旧表数据。

- [ ] **Step 3: 手工验证 Node MCP 关键路径**

Run:

```bash
python -m sau_mcp_launcher
curl http://127.0.0.1:5410/mcp/health
curl http://127.0.0.1:5410/mcp/capabilities
```

Expected:

- `health` 返回 `service=social-auto-upload-mcp`
- `capabilities.platforms` 包含 `tencent`
- `tools` 包含 `account_login/account_check/publish_submit/draft_save/schedule_create/task_cancel/task_retry`

- [ ] **Step 4: 手工验证 SSE**

Run:

```bash
curl -N http://127.0.0.1:5410/mcp/tasks/<task_id>/events
```

Expected:

- 至少观察到 `task.queued`
- 至少观察到 `task.running`
- 终态时观察到 `task.succeeded` 或 `task.failed`

- [ ] **Step 5: 汇总兼容清单并记录未纳入范围**

必须记录：

- `baijiahao`、`tiktok` 未纳入本次 Node MCP 工具面
- 平台内定时发布与服务端计划调度不叠加
- 图文多图按单子任务执行

## Spec 覆盖自检

- `Node MCP 服务层迁移`：Task 1、4、5、8 覆盖
- `SQLite 持久化`：Task 2、5、7 覆盖
- `Python 执行层保留`：Task 3、6、8 覆盖
- `草稿、批量发布、定时发布`：Task 2、6、7 覆盖
- `统一领域工具名`：Task 4、5、6 覆盖
- `父子任务与 SSE`：Task 5、6 覆盖
- `保持本地行为不变`：Task 3、8、最终验证覆盖

## 计划自检

- 已锁定入口接管方式，避免 `sau-mcp` 命令切换返工
- 已锁定 `tencent` 纳入能力矩阵，避免主线平台缺失
- 已锁定旧草稿导入策略，避免双真源
- 已锁定调度只负责延迟启动，避免双重定时语义
- 已锁定图文素材单元粒度，避免父子任务模型返工
- 已锁定服务重启后的失败恢复语义，避免运行中任务悬挂
