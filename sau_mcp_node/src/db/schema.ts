/**
 * MCP 数据库版本表。
 * 先固定为单版本迁移，后续新增结构时再按版本递增。
 */
export const CREATE_SCHEMA_MIGRATIONS_SQL = `
CREATE TABLE IF NOT EXISTS mcp_schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
`;

/**
 * 父任务表。
 * 统一承载账号任务、发布任务与控制任务的元数据。
 */
export const CREATE_MCP_TASKS_SQL = `
CREATE TABLE IF NOT EXISTS mcp_tasks (
  id TEXT PRIMARY KEY,
  tool_name TEXT NOT NULL,
  task_type TEXT NOT NULL,
  status TEXT NOT NULL,
  platform TEXT,
  content_type TEXT,
  trigger_mode TEXT,
  input_payload TEXT NOT NULL,
  result_payload TEXT,
  error_payload TEXT,
  progress_total INTEGER NOT NULL DEFAULT 0,
  progress_success INTEGER NOT NULL DEFAULT 0,
  progress_failed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  finished_at TEXT
);
`;

/**
 * 子任务表。
 * 按平台、账号与素材单元拆分发布执行单元。
 */
export const CREATE_MCP_TASK_CHILDREN_SQL = `
CREATE TABLE IF NOT EXISTS mcp_task_children (
  id TEXT PRIMARY KEY,
  parent_task_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  account_name TEXT NOT NULL,
  content_type TEXT NOT NULL,
  material_payload TEXT NOT NULL,
  schedule_at TEXT,
  status TEXT NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  result_payload TEXT,
  error_payload TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  finished_at TEXT,
  FOREIGN KEY(parent_task_id) REFERENCES mcp_tasks(id)
);
`;

/**
 * 事件表。
 * SSE 历史回放与重连都依赖这张表顺序读取事件。
 */
export const CREATE_MCP_TASK_EVENTS_SQL = `
CREATE TABLE IF NOT EXISTS mcp_task_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id TEXT NOT NULL,
  child_task_id TEXT,
  event_type TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT NOT NULL,
  data_payload TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
`;

/**
 * 新版 MCP 草稿表。
 * 保留 workspace 快照，同时为后续结构化字段预留列位。
 */
export const CREATE_MCP_PUBLISH_DRAFTS_SQL = `
CREATE TABLE IF NOT EXISTS mcp_publish_drafts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  legacy_draft_id INTEGER UNIQUE,
  name TEXT NOT NULL,
  platforms_payload TEXT,
  accounts_payload TEXT,
  content_type TEXT,
  materials_payload TEXT,
  metadata_payload TEXT,
  schedule_payload TEXT,
  workspace_payload TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
`;

/**
 * 定时计划表。
 * 服务内调度器会基于这张表恢复与触发待执行计划。
 */
export const CREATE_MCP_SCHEDULES_SQL = `
CREATE TABLE IF NOT EXISTS mcp_schedules (
  id TEXT PRIMARY KEY,
  draft_id INTEGER,
  source_payload TEXT NOT NULL,
  status TEXT NOT NULL,
  trigger_at TEXT NOT NULL,
  timezone TEXT NOT NULL,
  last_task_id TEXT,
  locked_at TEXT,
  locked_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
`;

/**
 * 账号快照表。
 * 这里只缓存最近一次校验结果，不替代真实 cookie 文件。
 */
export const CREATE_MCP_ACCOUNTS_SNAPSHOT_SQL = `
CREATE TABLE IF NOT EXISTS mcp_accounts_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  platform TEXT NOT NULL,
  account_name TEXT NOT NULL,
  account_file TEXT NOT NULL,
  last_check_status TEXT,
  last_check_at TEXT,
  last_error_payload TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(platform, account_name)
);
`;

/**
 * 当前 schema 版本。
 * Task 2 先落第一版，后续迁移通过新增版本处理。
 */
export const CURRENT_SCHEMA_VERSION = 1;

/**
 * 第一版 schema 语句清单。
 * 迁移器按顺序执行，保证最小数据库骨架完整。
 */
export const SCHEMA_V1_SQL: readonly string[] = [
  CREATE_SCHEMA_MIGRATIONS_SQL,
  CREATE_MCP_TASKS_SQL,
  CREATE_MCP_TASK_CHILDREN_SQL,
  CREATE_MCP_TASK_EVENTS_SQL,
  CREATE_MCP_PUBLISH_DRAFTS_SQL,
  CREATE_MCP_SCHEDULES_SQL,
  CREATE_MCP_ACCOUNTS_SNAPSHOT_SQL,
];
