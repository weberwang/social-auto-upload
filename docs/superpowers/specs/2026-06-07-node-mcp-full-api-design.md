# Node MCP 全量 API 补全设计

## 背景

当前项目已经提供一套 Python 实现的 MCP HTTP/SSE 服务，但对外只暴露了 `platform_login`、`platform_check` 两个低层工具，无法覆盖现有后台与 CLI 已具备的草稿、批量发布、定时发布、任务管理等能力。

本次设计目标不是重写平台执行逻辑，而是把 MCP 服务层全量迁移到 Node.js，并补齐面向主线平台的完整工具面，同时保持本地运行行为不变。

## 目标

- 将 MCP 服务层迁移到 Node.js。
- 保持本地平台执行能力继续复用 Python `helper`、`uploader`、`biliup`、`playwright`。
- 保持现有本地端口、账号文件路径、本地登录行为不变。
- 补齐草稿、批量发布、定时发布、任务查询、任务控制相关 API / MCP 工具。
- 统一查询、同步写、异步任务、SSE 事件流的协议模型。

## 非目标

- 不在本次设计中重写各平台 uploader。
- 不在本次设计中纳入 `baijiahao`、`tiktok` 等扩展平台。
- 不在本次设计中改变现有本地 cookie 文件布局。
- 不在本次设计中引入外部调度器、消息队列或远程任务服务。

## 范围

### 纳入平台

- `douyin`
- `kuaishou`
- `xiaohongshu`
- `bilibili`
- `tencent`

### 不纳入平台

- `baijiahao`
- `tiktok`
- 历史扩展 uploader 目录中的非主线入口

## 关键决策

### 接口风格

采用混合模式：

- 查询类接口使用同步返回。
- 纯本地数据写接口使用同步返回。
- 长耗时、需要进度和重试的操作使用异步任务。
- 任务进度与状态变化继续通过 SSE 输出。

### 工具命名

采用统一领域工具名，而不是按平台拆工具：

- 工具名表达“做什么”。
- 平台、内容类型、发布模式放入 `input`。
- 平台差异全部下沉到执行层与 Python bridge。

### 批量发布模型

采用父子任务模型：

- 一个 `publish_submit` 创建一个父任务。
- 父任务按 `平台 x 账号 x 素材单元` 展开子任务。
- 父任务负责总进度聚合。
- 子任务负责具体平台执行结果。

### 定时发布模型

采用服务内调度器 + SQLite：

- 定时计划存 SQLite。
- Node MCP 服务启动后恢复未完成计划。
- 到点后自动生成发布父任务并执行。
- 不依赖系统计划任务或外部 cron。

### 持久化模型

采用统一 SQLite 持久化：

- 草稿
- 任务
- 子任务
- 任务事件
- 定时计划
- 账号状态快照

## 总体架构

系统分为三层：

### Node MCP 网关层

职责：

- 对外提供 HTTP / SSE
- 参数校验
- 工具注册与调用分发
- 任务编排
- 定时调度
- 错误映射

### SQLite 持久化层

职责：

- 保存父任务、子任务、任务事件
- 保存发布草稿
- 保存定时计划
- 保存账号校验快照
- 为 SSE 回放和重启恢复提供数据基础

### Python 执行层

职责：

- 账号登录
- 账号校验
- 视频上传
- 图文上传
- `biliup` 调用
- 浏览器自动化
- 历史 cookie 文件兼容

设计原因：

- 现有平台能力已经深度绑定 Python `helper` 与 `uploader`。
- Node 只接管服务层和任务层，避免重写浏览器自动化逻辑。

## 对外工具清单

### 查询类工具

- `capabilities_get`
- `accounts_list`
- `draft_list`
- `draft_get`
- `task_list`
- `task_get`
- `task_children_list`
- `schedule_list`
- `schedule_get`

### 同步写工具

- `draft_save`
- `draft_delete`
- `schedule_create`
- `schedule_update`
- `schedule_delete`

### 异步任务工具

- `account_login`
- `account_check`
- `publish_submit`
- `task_cancel`
- `task_retry`

### 事件流

- `GET /mcp/tasks/:task_id/events`
- `GET /mcp/tasks/:task_id/children/:child_task_id/events`

## 数据模型

### 表一：`mcp_tasks`

用途：

- 保存父任务
- 保存账号类任务
- 保存发布类任务
- 保存控制类任务

核心字段：

- `id`
- `tool_name`
- `task_type`
- `status`
- `platform`
- `content_type`
- `trigger_mode`
- `input_payload`
- `result_payload`
- `error_payload`
- `progress_total`
- `progress_success`
- `progress_failed`
- `created_at`
- `started_at`
- `finished_at`

### 表二：`mcp_task_children`

用途：

- 保存父任务拆分出的执行单元

核心字段：

- `id`
- `parent_task_id`
- `platform`
- `account_name`
- `content_type`
- `material_payload`
- `schedule_at`
- `status`
- `attempt`
- `result_payload`
- `error_payload`
- `created_at`
- `started_at`
- `finished_at`

### 表三：`mcp_task_events`

用途：

- 保存父任务事件
- 保存子任务事件
- 支持 SSE 历史回放与重连

核心字段：

- `id`
- `task_id`
- `child_task_id`
- `event_type`
- `status`
- `message`
- `data_payload`
- `created_at`

### 表四：`mcp_publish_drafts`

用途：

- 保存发布草稿
- 保留复杂工作区数据
- 支持草稿转发布

核心字段：

- `id`
- `name`
- `platforms_payload`
- `accounts_payload`
- `content_type`
- `materials_payload`
- `metadata_payload`
- `schedule_payload`
- `workspace_payload`
- `created_at`
- `updated_at`

### 表五：`mcp_schedules`

用途：

- 保存待执行计划
- 记录计划与发布任务关系

核心字段：

- `id`
- `draft_id`
- `source_payload`
- `status`
- `trigger_at`
- `timezone`
- `last_task_id`
- `created_at`
- `updated_at`

### 表六：`mcp_accounts_snapshot`

用途：

- 缓存账号最近校验状态
- 不替代真实 cookie 文件

核心字段：

- `id`
- `platform`
- `account_name`
- `account_file`
- `last_check_status`
- `last_check_at`
- `last_error_payload`
- `created_at`
- `updated_at`

## 状态模型

### 任务状态

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

### 计划状态

- `pending`
- `running`
- `done`
- `failed`
- `cancelled`

设计原因：

- 不引入额外中间态，保持前端与客户端消费简单。
- 部分成功的父任务统一使用 `failed`，但通过聚合进度与结果详情表达成功/失败分布。

## API / MCP 契约

### 查询接口

- `GET /mcp/health`
- `GET /mcp/capabilities`
- `GET /mcp/accounts`
- `GET /mcp/drafts`
- `GET /mcp/drafts/:draft_id`
- `GET /mcp/tasks`
- `GET /mcp/tasks/:task_id`
- `GET /mcp/tasks/:task_id/children`
- `GET /mcp/schedules`
- `GET /mcp/schedules/:schedule_id`

### 同步写接口

- `POST /mcp/tools/draft_save`
- `POST /mcp/tools/draft_delete`
- `POST /mcp/tools/schedule_create`
- `POST /mcp/tools/schedule_update`
- `POST /mcp/tools/schedule_delete`

### 异步任务接口

- `POST /mcp/tools/account_login`
- `POST /mcp/tools/account_check`
- `POST /mcp/tools/publish_submit`
- `POST /mcp/tools/task_cancel`
- `POST /mcp/tools/task_retry`

### 兼容入口

保留现有兼容路径：

- `POST /mcp/tasks`

兼容策略：

- 老客户端继续通过 `tool + input` 调用。
- 新客户端优先使用 `/mcp/tools/:tool_name`。
- 两套入口内部走同一套 dispatch。

## 任务事件设计

### 父任务事件

- `task.queued`
- `task.running`
- `task.succeeded`
- `task.failed`
- `task.cancelled`

### 子任务事件

- `child_task.queued`
- `child_task.running`
- `child_task.succeeded`
- `child_task.failed`
- `child_task.cancelled`

### SSE 设计

- 事件统一从 `mcp_task_events` 顺序读取
- 先吐历史，再轮询新事件
- 任务到达终态且事件读完后关闭连接

设计原因：

- 避免依赖纯内存事件总线
- 服务重启后仍能回放完整历史

## 模块拆分

### `http`

职责：

- 路由
- 请求解析
- SSE 建连
- 响应输出

### `application`

职责：

- 用例编排
- 同步写与异步任务分流
- 连接 HTTP 层与执行层

### `domain`

职责：

- 任务、子任务、草稿、计划状态规则

### `repository`

职责：

- SQLite 读写

### `executor`

职责：

- 父子任务执行
- 重试
- 取消
- 进度聚合

### `bridge`

职责：

- 调 Python 子进程
- 映射 stdout / stderr / exit code

### `scheduler`

职责：

- 恢复待执行计划
- 到点触发发布
- 防重复执行

### `streaming`

职责：

- 基于事件表推 SSE

## Python Bridge 设计

Node 不直接拼复杂平台 CLI 参数，而是通过统一 JSON bridge 调 Python。

推荐桥接入口：

- `python -m sau_bridge account-login --json-input ...`
- `python -m sau_bridge account-check --json-input ...`
- `python -m sau_bridge publish-video --json-input ...`
- `python -m sau_bridge publish-note --json-input ...`

桥接约束：

- stdout 只输出标准 JSON
- stderr 只输出日志
- 非零退出码视为失败
- Node 统一做错误映射

设计原因：

- 避免平台差异重新泄漏回 Node
- 最大化复用现有 Python helper 与 uploader

## 执行流

### `account_login`

- 创建父任务
- 进入 `queued`
- 执行器拉起
- 进入 `running`
- 调 Python bridge
- 成功或失败写回任务与事件

### `account_check`

- 与 `account_login` 相同
- 成功结果额外写入账号快照表

### `publish_submit`

- 校验请求
- 如为草稿模式，先展开草稿
- 创建父任务
- 生成子任务
- 子任务进入 `queued`
- 执行器按并发策略执行
- 每个子任务调用 Python bridge
- 聚合父任务结果并写回事件

### `schedule_create`

- 仅写入计划表
- 不直接生成任务

### 定时触发

- 调度器加载 `pending` 计划
- 到点抢锁
- 抢锁成功后把计划状态改为 `running`
- 创建 `publish_submit` 父任务
- 父任务终态后回写计划状态

### `task_cancel`

- 取消未启动子任务
- 正在执行的子任务尝试安全终止
- 不再调度新子任务

### `task_retry`

- 基于原父任务生成新父任务
- 优先只重试失败子任务
- 原任务不覆写，只建立引用关系

## 并发策略

- 同一父任务默认并发数限制在 `1-3`
- 同一 `platform + account_name` 强制串行
- 不同平台允许有限并发
- 定时触发与手动触发共享执行池

设计原因：

- 浏览器自动化与账号上下文不适合高并发
- 同账号串行是稳定性边界

## 恢复策略

服务重启后：

- `drafts` 直接恢复
- `schedules` 恢复 `pending`
- `queued` 任务恢复为可继续调度
- `running` 任务统一标记为 `failed`
- 失败原因写为 `service_restarted_during_execution`

设计原因：

- 本地浏览器自动化上下文无法可靠恢复
- 强行恢复运行中子进程会引入隐性一致性问题

## 实施顺序

### 阶段一：冻结契约

- 冻结现有 MCP 路由、事件名、状态码、返回结构
- 冻结现有 CLI 主线平台能力

### 阶段二：补 SQLite 模型

- 新增任务、子任务、事件、草稿、计划、账号快照表

### 阶段三：实现 Node 基础服务

- 先落查询类和同步写接口

### 阶段四：实现 Python bridge

- 先打通账号类，再打通发布类

### 阶段五：实现父子任务执行器

- 补 `publish_submit`、SSE、取消、重试

### 阶段六：实现草稿能力

- 补草稿全链路

### 阶段七：实现调度器

- 补计划恢复、到点触发、防重

### 阶段八：补测试

- 路由契约
- 任务执行
- SSE
- 调度
- Python bridge

### 阶段九：切换入口

- `sau-mcp` 切到 Node 实现
- Python 旧 MCP 服务退为内部 bridge

## 验收标准

- 主线平台五个平台均可通过 MCP 完成账号操作和发布任务
- 草稿、批量发布、定时发布均已纳入 MCP
- 任务查询、子任务查询、事件订阅完整可用
- 本地账号文件、二维码、`biliup`、浏览器自动化行为不变
- 服务重启后草稿、计划、任务记录可恢复
- 现有兼容入口 `POST /mcp/tasks` 仍可用

## 风险与约束

### 风险

- Python bridge 的输出标准化是最高风险点
- SSE 终态收尾与重放是第二风险点
- Windows 下子进程编码、路径、虚拟环境定位是第三风险点

### 约束

- 不能放大现有平台执行面
- 不能在本次设计中重写 uploader
- 不能让 Node 直接接管浏览器自动化
- 不能改变现有本地运行习惯

## 结论

本次最合理的路线是：

- Node 接管 MCP 服务层、任务层、调度层、持久化层
- Python 保留平台执行层
- 通过统一 JSON bridge 打通两侧
- 以统一领域工具名补齐主线平台、草稿、批量发布、定时发布的完整 MCP 能力面

这一路线能在不改本地平台行为的前提下，完整补齐 MCP/API 工具面，并为后续扩展平台或前端任务看板提供稳定基础。
