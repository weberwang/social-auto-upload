import type { TaskStatus } from "./task.js";

/**
 * MCP 子任务实体。
 * 当前先覆盖列表查询和后续执行器要读写的最小字段。
 */
export type ChildTaskRecord = {
  id: string;
  parent_task_id: string;
  platform: string;
  account_name: string;
  content_type: string;
  material_payload: string;
  schedule_at: string | null;
  status: TaskStatus;
  attempt: number;
  result_payload: string | null;
  error_payload: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};
