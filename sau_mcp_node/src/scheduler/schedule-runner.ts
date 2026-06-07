import type { ScheduleRepository } from "../repositories/schedule-repository.js";
import type { TaskService } from "../services/task-service.js";

function nowIso(): string {
  return new Date().toISOString();
}

/**
 * 服务内调度器。
 * 当前先提供“扫描到点计划并触发一次父任务”的最小能力。
 */
export class ScheduleRunner {
  public constructor(
    private readonly scheduleRepository: ScheduleRepository,
    private readonly taskService: TaskService,
    private readonly runnerId: string,
  ) {}

  /**
   * 扫描并执行全部已到点计划。
   */
  public async runDueSchedules(referenceTimeIso: string = nowIso()): Promise<{ triggeredTaskCount: number }> {
    let triggeredTaskCount = 0;
    const dueSchedules = this.scheduleRepository.listDuePendingSchedules(referenceTimeIso);

    for (const schedule of dueSchedules) {
      const claimed = this.scheduleRepository.claimSchedule(schedule.id, referenceTimeIso, this.runnerId);
      if (!claimed) {
        continue;
      }

      const sourcePayload = JSON.parse(schedule.source_payload) as unknown;
      try {
        const taskResult = await this.taskService.createPublishTask(sourcePayload);
        this.scheduleRepository.completeSchedule(schedule.id, "done", taskResult.task_id);
        triggeredTaskCount += 1;
      } catch {
        this.scheduleRepository.completeSchedule(schedule.id, "failed", null);
      }
    }

    return { triggeredTaskCount };
  }
}
