import type Database from "better-sqlite3";

import type { TaskRecord, TaskStatus } from "../domain/task.js";

export type CreateTaskInput = {
  id: string;
  tool_name: string;
  task_type: string;
  status: TaskStatus;
  platform?: string | null;
  content_type?: string | null;
  trigger_mode?: string | null;
  input_payload: string;
};

export type CompleteTaskInput = {
  taskId: string;
  resultPayload?: string | null;
  errorPayload?: string | null;
  startedAt?: string | null;
  finishedAt?: string | null;
};

/**
 * 父任务仓储。
 * 当前先实现创建、详情和列表，供兼容任务入口与查询接口复用。
 */
export class TaskRepository {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 创建父任务记录。
   */
  public createTask(input: CreateTaskInput): void {
    this.database
      .prepare(
        `
          INSERT INTO mcp_tasks (
            id,
            tool_name,
            task_type,
            status,
            platform,
            content_type,
            trigger_mode,
            input_payload
          )
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `,
      )
      .run(
        input.id,
        input.tool_name,
        input.task_type,
        input.status,
        input.platform ?? null,
        input.content_type ?? null,
        input.trigger_mode ?? null,
        input.input_payload,
      );
  }

  /**
   * 更新任务状态。
   */
  public updateStatus(taskId: string, status: TaskStatus): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET status = ?
          WHERE id = ?
        `,
      )
      .run(status, taskId);
  }

  /**
   * 把任务推进到运行中，并记录开始时间。
   */
  public markRunning(taskId: string, startedAt: string): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET status = 'running', started_at = ?
          WHERE id = ?
        `,
      )
      .run(startedAt, taskId);
  }

  /**
   * 把任务推进到成功并保存结果。
   */
  public markSucceeded(input: CompleteTaskInput): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET status = 'succeeded',
              result_payload = ?,
              started_at = COALESCE(started_at, ?),
              finished_at = ?
          WHERE id = ?
        `,
      )
      .run(input.resultPayload ?? null, input.startedAt ?? null, input.finishedAt ?? null, input.taskId);
  }

  /**
   * 把任务推进到失败并保存错误。
   */
  public markFailed(input: CompleteTaskInput): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET status = 'failed',
              error_payload = ?,
              started_at = COALESCE(started_at, ?),
              finished_at = ?
          WHERE id = ?
        `,
      )
      .run(input.errorPayload ?? null, input.startedAt ?? null, input.finishedAt ?? null, input.taskId);
  }

  /**
   * 把任务推进到取消态。
   */
  public markCancelled(taskId: string, finishedAt: string): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET status = 'cancelled',
              finished_at = ?
          WHERE id = ?
        `,
      )
      .run(finishedAt, taskId);
  }

  /**
   * 更新父任务聚合进度。
   */
  public updateProgress(taskId: string, total: number, success: number, failed: number): void {
    this.database
      .prepare(
        `
          UPDATE mcp_tasks
          SET progress_total = ?,
              progress_success = ?,
              progress_failed = ?
          WHERE id = ?
        `,
      )
      .run(total, success, failed, taskId);
  }

  /**
   * 查询单个任务。
   */
  public getTask(taskId: string): TaskRecord | null {
    return (
      this.database
        .prepare<[string], TaskRecord>(
          `
            SELECT *
            FROM mcp_tasks
            WHERE id = ?
          `,
        )
        .get(taskId) ?? null
    );
  }

  /**
   * 返回任务列表。
   */
  public listTasks(): TaskRecord[] {
    return this.database
      .prepare<[], TaskRecord>(
        `
          SELECT *
          FROM mcp_tasks
          ORDER BY datetime(created_at) DESC, id DESC
        `,
      )
      .all();
  }
}
