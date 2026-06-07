/**
 * MCP 父任务状态。
 * 先固定为当前计划阶段需要的终态和中间态，避免到处手写裸字符串。
 */
export type TaskStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

/**
 * MCP 父任务实体。
 * 当前先承载仓储与路由层都需要的最小字段。
 */
export type TaskRecord = {
  id: string;
  tool_name: string;
  task_type: string;
  status: TaskStatus;
  platform: string | null;
  content_type: string | null;
  trigger_mode: string | null;
  input_payload: string;
  result_payload: string | null;
  error_payload: string | null;
  progress_total: number;
  progress_success: number;
  progress_failed: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};
