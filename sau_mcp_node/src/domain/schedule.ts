/**
 * 定时计划状态。
 * 当前只先覆盖主线的 pending/running/done/failed/cancelled。
 */
export type ScheduleStatus = "pending" | "running" | "done" | "failed" | "cancelled";
