import { randomUUID } from "node:crypto";

import type Database from "better-sqlite3";

import type { ScheduleStatus } from "../domain/schedule.js";

export type ScheduleRecord = {
  id: string;
  draft_id: number | null;
  source_payload: string;
  status: string;
  trigger_at: string;
  timezone: string;
  last_task_id: string | null;
  locked_at: string | null;
  locked_by: string | null;
  created_at: string;
  updated_at: string;
};

export type CreateScheduleInput = {
  draft_id?: number | null;
  source_payload: string;
  trigger_at: string;
  timezone: string;
};

/**
 * 定时计划仓储。
 * 当前负责计划 CRUD、到点抢占和执行结果回写。
 */
export class ScheduleRepository {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 创建计划。
   */
  public createSchedule(input: CreateScheduleInput): { schedule_id: string; status: ScheduleStatus } {
    const scheduleId = `schedule_${randomUUID()}`;
    this.database
      .prepare(
        `
          INSERT INTO mcp_schedules (
            id,
            draft_id,
            source_payload,
            status,
            trigger_at,
            timezone
          )
          VALUES (?, ?, ?, 'pending', ?, ?)
        `,
      )
      .run(scheduleId, input.draft_id ?? null, input.source_payload, input.trigger_at, input.timezone);
    return { schedule_id: scheduleId, status: "pending" };
  }

  /**
   * 更新计划。
   */
  public updateSchedule(scheduleId: string, sourcePayload: string, triggerAt: string, timezone: string): boolean {
    const result = this.database
      .prepare(
        `
          UPDATE mcp_schedules
          SET source_payload = ?,
              trigger_at = ?,
              timezone = ?,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ? AND status = 'pending'
        `,
      )
      .run(sourcePayload, triggerAt, timezone, scheduleId);
    return result.changes > 0;
  }

  /**
   * 删除待执行计划。
   */
  public deleteSchedule(scheduleId: string): boolean {
    const result = this.database
      .prepare(
        `
          DELETE FROM mcp_schedules
          WHERE id = ? AND status = 'pending'
        `,
      )
      .run(scheduleId);
    return result.changes > 0;
  }

  /**
   * 查询单个计划。
   */
  public getSchedule(scheduleId: string): ScheduleRecord | null {
    return (
      this.database
        .prepare<[string], ScheduleRecord>(
          `
            SELECT *
            FROM mcp_schedules
            WHERE id = ?
          `,
        )
        .get(scheduleId) ?? null
    );
  }

  /**
   * 列出全部计划。
   */
  public listSchedules(): ScheduleRecord[] {
    return this.database
      .prepare<[], ScheduleRecord>(
        `
          SELECT *
          FROM mcp_schedules
          ORDER BY datetime(trigger_at) ASC, id ASC
        `,
      )
      .all();
  }

  /**
   * 查找已到点的待执行计划。
   */
  public listDuePendingSchedules(nowIso: string): ScheduleRecord[] {
    return this.database
      .prepare<[string], ScheduleRecord>(
        `
          SELECT *
          FROM mcp_schedules
          WHERE status = 'pending' AND datetime(trigger_at) <= datetime(?)
          ORDER BY datetime(trigger_at) ASC, id ASC
        `,
      )
      .all(nowIso);
  }

  /**
   * 抢占计划执行权。
   * 只有 pending 且未上锁的计划能被成功抢占。
   */
  public claimSchedule(scheduleId: string, lockedAt: string, lockedBy: string): boolean {
    const result = this.database
      .prepare(
        `
          UPDATE mcp_schedules
          SET status = 'running',
              locked_at = ?,
              locked_by = ?,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ? AND status = 'pending' AND locked_at IS NULL
        `,
      )
      .run(lockedAt, lockedBy, scheduleId);
    return result.changes > 0;
  }

  /**
   * 回写计划终态。
   */
  public completeSchedule(scheduleId: string, status: Extract<ScheduleStatus, "done" | "failed" | "cancelled">, lastTaskId: string | null): void {
    this.database
      .prepare(
        `
          UPDATE mcp_schedules
          SET status = ?,
              last_task_id = ?,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `,
      )
      .run(status, lastTaskId, scheduleId);
  }
}
