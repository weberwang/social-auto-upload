import type Database from "better-sqlite3";

import type { TaskStatus } from "../domain/task.js";

export type TaskEventRecord = {
  id: number;
  task_id: string;
  child_task_id: string | null;
  event_type: string;
  status: TaskStatus;
  message: string;
  data_payload: string | null;
  created_at: string;
};

export type CreateTaskEventInput = {
  task_id: string;
  child_task_id?: string | null;
  event_type: string;
  status: TaskStatus;
  message: string;
  data_payload?: string | null;
};

/**
 * 任务事件仓储。
 * 基础 SSE 回放与兼容任务入口都依赖这里顺序读取事件。
 */
export class TaskEventRepository {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 追加一条任务事件。
   */
  public appendEvent(input: CreateTaskEventInput): void {
    this.database
      .prepare(
        `
          INSERT INTO mcp_task_events (
            task_id,
            child_task_id,
            event_type,
            status,
            message,
            data_payload
          )
          VALUES (?, ?, ?, ?, ?, ?)
        `,
      )
      .run(
        input.task_id,
        input.child_task_id ?? null,
        input.event_type,
        input.status,
        input.message,
        input.data_payload ?? null,
      );
  }

  /**
   * 返回指定任务的事件历史。
   */
  public listByTask(taskId: string): TaskEventRecord[] {
    return this.database
      .prepare<[string], TaskEventRecord>(
        `
          SELECT *
          FROM mcp_task_events
          WHERE task_id = ?
          ORDER BY id ASC
        `,
      )
      .all(taskId);
  }
}
