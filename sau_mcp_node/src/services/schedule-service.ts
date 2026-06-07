import type Database from "better-sqlite3";

import { ScheduleRepository, type ScheduleRecord } from "../repositories/schedule-repository.js";

/**
 * 定时计划查询服务。
 * Task 4 先提供查询能力，写操作和调度逻辑在后续任务补齐。
 */
export class ScheduleService {
  private readonly scheduleRepository: ScheduleRepository;

  public constructor(database: Database.Database) {
    this.scheduleRepository = new ScheduleRepository(database);
  }

  /**
   * 返回计划列表。
   */
  public listSchedules(): ScheduleRecord[] {
    return this.scheduleRepository.listSchedules();
  }

  /**
   * 返回单个计划详情。
   */
  public getSchedule(scheduleId: string): ScheduleRecord | null {
    return this.scheduleRepository.getSchedule(scheduleId);
  }

  /**
   * 创建计划。
   */
  public createSchedule(payload: unknown): { schedule_id: string; status: string } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("schedule payload must be an object");
    }
    const value = payload as {
      draft_id?: unknown;
      source_payload?: unknown;
      trigger_at?: unknown;
      timezone?: unknown;
    };
    if (typeof value.trigger_at !== "string" || !value.trigger_at.trim()) {
      throw new Error("trigger_at is required");
    }
    if (typeof value.timezone !== "string" || !value.timezone.trim()) {
      throw new Error("timezone is required");
    }
    if (!value.source_payload || typeof value.source_payload !== "object" || Array.isArray(value.source_payload)) {
      throw new Error("source_payload must be an object");
    }

    return this.scheduleRepository.createSchedule({
      draft_id: value.draft_id == null ? null : Number.parseInt(String(value.draft_id), 10),
      source_payload: JSON.stringify(value.source_payload),
      trigger_at: value.trigger_at,
      timezone: value.timezone,
    });
  }

  /**
   * 更新待执行计划。
   */
  public updateSchedule(payload: unknown): { schedule_id: string; status: "updated" } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("schedule update payload must be an object");
    }
    const value = payload as {
      schedule_id?: unknown;
      source_payload?: unknown;
      trigger_at?: unknown;
      timezone?: unknown;
    };
    if (typeof value.schedule_id !== "string" || !value.schedule_id.trim()) {
      throw new Error("schedule_id is required");
    }
    if (typeof value.trigger_at !== "string" || !value.trigger_at.trim()) {
      throw new Error("trigger_at is required");
    }
    if (typeof value.timezone !== "string" || !value.timezone.trim()) {
      throw new Error("timezone is required");
    }
    if (!value.source_payload || typeof value.source_payload !== "object" || Array.isArray(value.source_payload)) {
      throw new Error("source_payload must be an object");
    }

    const updated = this.scheduleRepository.updateSchedule(
      value.schedule_id,
      JSON.stringify(value.source_payload),
      value.trigger_at,
      value.timezone,
    );
    if (!updated) {
      throw new Error("schedule not found or not pending");
    }
    return { schedule_id: value.schedule_id, status: "updated" };
  }

  /**
   * 删除待执行计划。
   */
  public deleteSchedule(payload: unknown): { schedule_id: string; status: "deleted" } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("schedule delete payload must be an object");
    }
    const scheduleId = (payload as { schedule_id?: unknown }).schedule_id;
    if (typeof scheduleId !== "string" || !scheduleId.trim()) {
      throw new Error("schedule_id is required");
    }

    const deleted = this.scheduleRepository.deleteSchedule(scheduleId);
    if (!deleted) {
      throw new Error("schedule not found or not pending");
    }
    return { schedule_id: scheduleId, status: "deleted" };
  }
}
