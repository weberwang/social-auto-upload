import type { ChildTaskRepository } from "../repositories/child-task-repository.js";
import type { TaskEventRepository } from "../repositories/task-event-repository.js";
import type { TaskRepository } from "../repositories/task-repository.js";

function nowIso(): string {
  return new Date().toISOString();
}

/**
 * 任务控制执行器。
 * 当前先支持取消已受理但未完成的任务。
 */
export class TaskControlExecutor {
  public constructor(
    private readonly taskRepository: TaskRepository,
    private readonly childTaskRepository: ChildTaskRepository,
    private readonly taskEventRepository: TaskEventRepository,
  ) {}

  /**
   * 取消任务。
   * 当前策略先把父任务和未开始子任务标记为 cancelled。
   */
  public cancelTask(taskId: string): { task_id: string; status: "cancelled"; cancelled_children: number } {
    const finishedAt = nowIso();
    const cancelledChildren = this.childTaskRepository.cancelQueuedByParentTask(taskId, finishedAt);
    this.taskRepository.markCancelled(taskId, finishedAt);
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.cancelled",
      status: "cancelled",
      message: "任务已取消",
      data_payload: JSON.stringify({ cancelled_children: cancelledChildren }),
    });
    return {
      task_id: taskId,
      status: "cancelled",
      cancelled_children: cancelledChildren,
    };
  }
}
