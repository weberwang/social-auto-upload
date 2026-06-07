import type Database from "better-sqlite3";

import type { ChildTaskRecord } from "../domain/child-task.js";
import type { TaskStatus } from "../domain/task.js";

export type CreateChildTaskInput = {
  id: string;
  parent_task_id: string;
  platform: string;
  account_name: string;
  content_type: string;
  material_payload: string;
  schedule_at?: string | null;
  status: TaskStatus;
};

/**
 * 子任务仓储。
 * Task 5 先实现按父任务查询列表，执行创建放到后续任务补齐。
 */
export class ChildTaskRepository {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 返回指定父任务下的全部子任务。
   */
  public listByParentTask(parentTaskId: string): ChildTaskRecord[] {
    return this.database
      .prepare<[string], ChildTaskRecord>(
        `
          SELECT *
          FROM mcp_task_children
          WHERE parent_task_id = ?
          ORDER BY datetime(created_at) ASC, id ASC
        `,
      )
      .all(parentTaskId);
  }

  /**
   * 批量创建子任务。
   */
  public createMany(inputs: CreateChildTaskInput[]): void {
    const statement = this.database.prepare(
      `
        INSERT INTO mcp_task_children (
          id,
          parent_task_id,
          platform,
          account_name,
          content_type,
          material_payload,
          schedule_at,
          status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `,
    );

    const insertMany = this.database.transaction((items: CreateChildTaskInput[]) => {
      for (const item of items) {
        statement.run(
          item.id,
          item.parent_task_id,
          item.platform,
          item.account_name,
          item.content_type,
          item.material_payload,
          item.schedule_at ?? null,
          item.status,
        );
      }
    });

    insertMany(inputs);
  }

  /**
   * 把子任务推进到运行中。
   */
  public markRunning(childTaskId: string, startedAt: string): void {
    this.database
      .prepare(
        `
          UPDATE mcp_task_children
          SET status = 'running', started_at = ?
          WHERE id = ?
        `,
      )
      .run(startedAt, childTaskId);
  }

  /**
   * 把子任务推进到成功。
   */
  public markSucceeded(childTaskId: string, resultPayload: string | null, finishedAt: string): void {
    this.database
      .prepare(
        `
          UPDATE mcp_task_children
          SET status = 'succeeded',
              result_payload = ?,
              finished_at = ?
          WHERE id = ?
        `,
      )
      .run(resultPayload, finishedAt, childTaskId);
  }

  /**
   * 把子任务推进到失败。
   */
  public markFailed(childTaskId: string, errorPayload: string | null, finishedAt: string): void {
    this.database
      .prepare(
        `
          UPDATE mcp_task_children
          SET status = 'failed',
              error_payload = ?,
              finished_at = ?
          WHERE id = ?
        `,
      )
      .run(errorPayload, finishedAt, childTaskId);
  }

  /**
   * 取消尚未开始的子任务。
   */
  public cancelQueuedByParentTask(parentTaskId: string, finishedAt: string): number {
    const result = this.database
      .prepare(
        `
          UPDATE mcp_task_children
          SET status = 'cancelled',
              finished_at = ?
          WHERE parent_task_id = ? AND status = 'queued'
        `,
      )
      .run(finishedAt, parentTaskId);
    return result.changes;
  }
}
