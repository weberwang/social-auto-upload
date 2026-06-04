# social-auto-upload MCP Server 设计稿

## 背景

当前仓库主线能力已经逐步收敛到 `sau` CLI 和各平台 uploader，但对 AI 客户端的接入方式仍主要依赖：

- 直接读取仓库文档与 skill
- 通过 CLI 间接调用平台能力
- 历史 Web 接口提供的非标准上传与登录流程

这几条路径都能工作，但都不适合作为统一、标准、可被多个客户端复用的服务端协议层。

本次设计目标是在不破坏当前 CLI 主线的前提下，为项目新增一套独立的 `HTTP/SSE` 型 `MCP Server`，用于向 `Codex`、`Claude Code`、`OpenClaw` 等客户端暴露标准化工具能力与高层业务能力。

## 目标

新增一套独立的 MCP 服务能力，满足以下要求：

- 使用 `HTTP + SSE` 作为传输方式
- 同时暴露底层工具能力与高层业务能力
- 所有实际动作都走异步任务队列
- 任务执行过程可通过 SSE 持续订阅
- CLI 与 MCP 共享业务能力，不允许 MCP 退化成 shell 包装层
- 第一版仅覆盖当前主线平台：`douyin`、`kuaishou`、`xiaohongshu`、`bilibili`

## 非目标

以下内容不在本次第一版范围内：

- 不做分布式任务系统
- 不做多进程/多机器调度
- 不把历史 Web 后端整体重写为新 MCP 服务
- 不在第一版接入 `tencent`、`baijiahao`、`tiktok`
- 不支持任意 shell 命令透传
- 不把整个 CLI 参数树原样暴露为协议字段

## 方案选型

本次设计在 3 种方案中选择方案 2：

1. 直接在现有 `sau_backend.py` 中继续叠加 MCP 路由
2. 新建独立 `sau_mcp_server` 模块，复用 Flask 运行时
3. 新建完全独立的后端服务，并逐步替换历史 Web 后端

最终选择方案 2，原因如下：

- 当前仓库已经具备 Flask 与 SSE 基础，复用运行时成本最低
- `sau_backend.py` 已承担过多历史职责，不适合继续增长
- 新增独立模块可以把协议层、任务层、业务层清晰拆开
- 该方案与“CLI 主线优先，旧 Web 非主线”的项目方向一致
- 后续若要进一步独立服务，也能平滑迁移

## 总体架构

新增一套独立模块 `sau_mcp_server`，作为 MCP 协议入口。整体调用链如下：

1. 客户端调用 `/mcp` 下的 HTTP 接口
2. 协议层完成参数校验、工具分发、任务创建
3. 任务进入本地异步任务队列
4. worker 调用共享 service 层
5. service 层调用现有 uploader 能力完成登录、校验或上传
6. 执行过程中的状态、日志、产物通过 SSE 推送
7. 客户端既可实时订阅，也可通过任务查询接口补拉状态

### 分层边界

- `HTTP/SSE 协议层`
  - 负责路由、请求解析、事件输出、MCP 协议适配
- `任务层`
  - 负责任务状态流转、worker 调度、取消控制、事件发布
- `service 层`
  - 负责平台无关的业务编排，不关心 CLI 或 HTTP 来源
- `平台适配层`
  - 负责调用现有 uploader / runtime / cookie 检查等实际执行能力

## 任务模型

### 任务类型

底层工具任务：

- `platform.login`
- `platform.check`
- `platform.upload_video`
- `platform.upload_note`

高层业务任务：

- `account.validate`
- `publish.create`
- `publish.batch_create`

### 任务状态

统一状态机如下：

- `queued`
- `running`
- `waiting_for_user`
- `succeeded`
- `failed`
- `cancelled`

其中 `waiting_for_user` 是必要状态，用于表示以下情况：

- 等待扫码
- 等待验证码
- 等待平台侧人工确认
- 等待用户处理本地交互步骤

如果没有该状态，客户端会把长耗时但正常等待的任务误判为卡死或失败。

### 任务字段

第一版任务实体至少保存以下字段：

- `task_id`
- `task_type`
- `platform`
- `account_name`
- `status`
- `input`
- `result`
- `error`
- `progress_message`
- `created_at`
- `updated_at`
- `finished_at`
- `parent_task_id`

设计原因：

- `input/result/error` 用于结构化回放任务上下文
- `progress_message` 用于给客户端直接展示最新可读状态
- `parent_task_id` 用于支持高层批量任务拆分为多个子任务

## 事件模型

所有任务过程都通过 SSE 事件发布。第一版事件类型如下：

- `task.created`
- `task.started`
- `task.progress`
- `task.waiting`
- `task.succeeded`
- `task.failed`
- `task.cancelled`
- `task.artifact`
- `task.heartbeat`

### 事件结构

统一事件结构如下：

```json
{
  "event": "task.progress",
  "task_id": "task_01J...",
  "status": "running",
  "message": "已打开平台发布页，等待上传完成",
  "timestamp": "2026-06-05T10:20:30+08:00",
  "data": {}
}
```

### 特殊事件

`task.waiting`：

- 用于表达任务正在等待用户完成外部交互
- 客户端应将其展示为“等待用户操作”，而不是错误

`task.artifact`：

- 用于返回二维码图片路径、日志路径、截图路径等产物
- 客户端可以根据 `artifact_type` 做额外展示

示例：

```json
{
  "event": "task.artifact",
  "task_id": "task_01J...",
  "status": "waiting_for_user",
  "message": "请扫码完成登录",
  "timestamp": "2026-06-05T10:20:30+08:00",
  "data": {
    "artifact_type": "image",
    "path": "D:/Git/social-auto-upload/qrcode.png"
  }
}
```

## 对外能力边界

### Tools

第一版对外开放以下工具：

- `platform_login`
  - 入参：`platform`、`account_name`、`headless`
  - 行为：创建登录任务并返回 `task_id`
- `platform_check`
  - 入参：`platform`、`account_name`
  - 行为：创建账号校验任务并返回 `task_id`
- `upload_video`
  - 入参：`platform`、`account_name`、`file`、`title`、`desc`、`tags`、`schedule`、平台扩展字段
  - 行为：创建视频上传任务并返回 `task_id`
- `upload_note`
  - 入参：`platform`、`account_name`、`images`、`title`、`note`、`tags`、`schedule`
  - 行为：创建图文上传任务并返回 `task_id`
- `create_publish_task`
  - 入参：高层发布任务定义，允许一个父任务拆解为多个子任务
  - 行为：创建父任务并调度子任务
- `cancel_task`
  - 入参：`task_id`
  - 行为：取消尚未执行或可安全中断的任务

### Resources

第一版对外开放以下资源：

- `platforms`
  - 返回平台列表与能力矩阵
- `accounts`
  - 返回全部账号列表
- `accounts/{platform}`
  - 返回某平台账号列表
- `accounts/{platform}/{account_name}`
  - 返回单账号基础信息与最近状态
- `tasks`
  - 返回最近任务列表
- `tasks/{task_id}`
  - 返回任务详情
- `tasks/{task_id}/events`
  - 返回单任务事件历史快照
- `capabilities`
  - 返回当前服务版本、可用工具、字段约束、平台支持情况

### 边界原则

- 会触发副作用、会启动浏览器、会创建任务的能力放到 `tools`
- 纯读取、纯列举、纯状态查询能力放到 `resources`

这样设计的原因是：

- 客户端可以先通过 `resources` 建立上下文
- 真正的执行动作统一进入任务体系
- 协议层不会被历史 Web 接口的自由形态参数污染

## HTTP / SSE 路由设计

所有新服务路由统一挂载在 `/mcp` 前缀下，与历史 Web 路由隔离。

### HTTP 路由

- `GET /mcp/health`
  - 返回健康状态、版本、队列长度
- `GET /mcp/capabilities`
  - 返回能力矩阵与工具清单
- `GET /mcp/platforms`
  - 返回平台列表
- `GET /mcp/accounts`
  - 返回账号列表
- `GET /mcp/accounts/<platform>`
  - 返回平台账号列表
- `GET /mcp/tasks`
  - 返回任务列表，支持按状态、平台、账号、类型过滤
- `GET /mcp/tasks/<task_id>`
  - 返回任务详情
- `POST /mcp/tasks`
  - 统一任务创建入口
- `POST /mcp/tasks/<task_id>/cancel`
  - 取消任务

### SSE 路由

- `GET /mcp/tasks/<task_id>/events`
  - 订阅单任务事件流
- `GET /mcp/events`
  - 订阅全局事件流

### 统一任务创建协议

不为每个工具单独创建 HTTP endpoint，而是统一通过：

- `POST /mcp/tasks`

示例请求：

```json
{
  "tool": "upload_video",
  "input": {
    "platform": "douyin",
    "account_name": "creator",
    "file": "D:/Git/social-auto-upload/videos/demo.mp4",
    "title": "示例标题",
    "desc": "示例简介",
    "tags": ["测试"],
    "schedule": null
  }
}
```

示例响应：

```json
{
  "task_id": "task_01J...",
  "status": "queued"
}
```

设计原因：

- HTTP 层保持统一入口，避免路由树过早膨胀
- `tool + input` 的结构与 MCP 工具抽象天然对齐
- 后续新增工具时无需继续扩张路由集合

## 代码结构设计

第一版建议新增如下模块：

- `sau_mcp_server/__init__.py`
- `sau_mcp_server/app.py`
- `sau_mcp_server/config.py`
- `sau_mcp_server/http/routes.py`
- `sau_mcp_server/http/sse.py`
- `sau_mcp_server/models/task.py`
- `sau_mcp_server/repositories/task_repository.py`
- `sau_mcp_server/queue/task_queue.py`
- `sau_mcp_server/services/platform_service.py`
- `sau_mcp_server/services/account_service.py`
- `sau_mcp_server/services/capability_service.py`
- `sau_mcp_server/tools/dispatcher.py`

### 拆分原则

`sau_backend.py` 现有职责过多，不能继续作为新协议主入口；`sau_cli.py` 也不应继续承担全部业务逻辑。

因此需要先抽共享 service 层，再让不同入口复用：

- CLI 调 service
- MCP 调 service
- 历史 Web 若保留，也逐步改为调 service

禁止以下反向依赖：

- MCP 通过 shell 调 `sau`
- HTTP 层直接调 `argparse.Namespace`
- CLI 和 MCP 分别维护两套上传编排逻辑

## 与现有代码的集成策略

### CLI 侧调整

`sau_cli.py` 后续只保留以下职责：

- 命令解析
- 参数转换
- 调用共享 service
- 打印结果

当前散落在 CLI 中的登录、校验、上传业务调用，需要逐步下沉到 service 层。

### 历史 Web 侧策略

`sau_backend.py` 暂不整体重写，只做以下处理：

- 保留现有旧接口，避免影响历史调用方
- 不再向其主文件中继续堆叠 MCP 逻辑
- 新 MCP 服务复用 Flask，但在独立模块中注册路由

### 平台支持范围

第一版仅接入：

- `douyin`
- `kuaishou`
- `xiaohongshu`
- `bilibili`

原因：

- 这 4 个平台是当前 CLI 主线与文档主线
- 先把协议、状态、任务、事件模型跑稳，再扩平台更可控

## 持久化策略

第一版推荐：

- 运行中的队列使用内存结构
- 任务元数据支持内存实现
- 同时预留 SQLite 持久化实现接口

设计原因：

- 当前项目的瓶颈主要在浏览器自动化，不在队列吞吐
- 先验证任务模型、事件模型、错误语义是否成立更重要
- 预留 repository 抽象后，后续可无缝切换到 SQLite 持久化

### 第一版允许的简化

- 服务重启后，运行中任务不恢复
- 任务历史可以只保留最近一段时间
- 取消任务先支持“未开始任务取消”和“软取消”

## 错误处理与边界条件

### 错误分类

第一版需要区分以下错误：

- 参数错误
- 文件不存在
- 账号不存在
- cookie 缺失或失效
- 平台登录等待用户操作
- 平台页面结构变更导致失败
- worker 内部异常

### 处理原则

- 参数类错误在入队前直接返回 4xx
- 执行期错误统一反映到任务状态 `failed`
- 需要用户介入的情况使用 `waiting_for_user`，而不是失败
- 结构化返回 `error.code`、`error.message`、`error.details`

### Bilibili 特殊约束

需要延续当前 CLI 约束：

- 非交互环境下不强行代跑 Bilibili 登录
- 遇到该限制时，应通过任务事件明确提示用户在本地真实终端执行

## 并发与安全限制

第一版不追求高并发，而优先追求稳定性。

建议策略：

- 默认单进程 worker
- 按平台做基础限流，避免同平台多浏览器竞争资源
- 文件路径仅允许本地绝对路径或工作区内可访问路径
- SSE 只传状态事件，不传大文件内容

设计原因：

- 浏览器自动化流程天然重、慢、易受环境影响
- 过早引入高并发会放大 cookie、浏览器、文件句柄、页面状态冲突
- 限制输入路径和传输范围可以降低路径注入与资源泄漏风险

## 测试策略

第一版测试按 3 层组织：

### 1. 单元测试

- 任务状态流转
- 事件编码
- 工具分发
- service 请求模型校验

### 2. 接口测试

- `POST /mcp/tasks`
- `GET /mcp/tasks/<task_id>`
- `GET /mcp/tasks/<task_id>/events`
- `GET /mcp/capabilities`

### 3. 平台编排测试

通过 mock service 或 mock uploader 验证：

- 登录任务是否正确发出等待事件
- 上传任务是否正确发出进度与完成事件
- 高层发布任务是否能拆成父子任务

测试重点：

- 先验证协议层与任务层行为
- 尽量避免在自动化测试中直接依赖真实平台页面

## 实现顺序

建议分 5 步实施：

1. 抽出共享 service 层
2. 建立任务模型、事件模型、队列与 repository
3. 落 `/mcp` HTTP 与 SSE 基础路由
4. 接入第一批底层工具：`platform_login`、`platform_check`、`upload_video`、`upload_note`
5. 接入高层工具：`create_publish_task`

顺序原因：

- 先解决复用边界，再解决协议层
- 先让最小闭环跑通，再叠加高层业务编排
- 每一步都可以独立测试和回归验证

## 验收标准

第一版完成后，以下结果应成立：

- 可以通过 HTTP 创建登录、校验、上传任务
- 可以通过 SSE 实时订阅任务事件
- 可以通过任务查询接口补拉状态
- CLI 与 MCP 共享 service 层，而不是各自维护一套上传调用逻辑
- 第一版 4 个平台可通过统一任务协议接入
- 历史 Web 接口不被本次改造破坏

## 风险与后续演进

### 主要风险

- 现有 CLI 业务逻辑与参数解析耦合较深，抽 service 需要谨慎
- 某些平台登录流程的“等待用户交互”语义不完全统一
- 历史 Web 数据结构与 CLI 主线的数据结构不一致
- 浏览器自动化本身仍受平台页面变动影响

### 缓解方式

- 先以 CLI 主线为准，避免新协议依赖历史 Web 行为
- 统一 `waiting_for_user` 与 `task.artifact` 语义
- 对 service 层做明确 request/response 模型约束
- 用协议层与队列层测试覆盖核心状态流转

### 后续演进方向

- 增加 SQLite 任务持久化
- 扩展 `tencent`、`baijiahao`、`tiktok`
- 引入更细粒度的并发控制
- 在能力矩阵中暴露平台字段 schema 与 UI hints

## 最终结论

本次 `MCP Server` 设计应采用以下落地路线：

- 新建独立 `sau_mcp_server` 模块
- 基于 Flask 提供 `/mcp` 下的 `HTTP + SSE` 服务
- 统一使用异步任务队列承载所有执行动作
- 通过共享 service 层打通 CLI 与 MCP
- 第一版仅接入 `douyin`、`kuaishou`、`xiaohongshu`、`bilibili`

这是当前仓库在“保持主线稳定、降低耦合、面向 AI 客户端标准化接入”三者之间的最稳妥方案。
