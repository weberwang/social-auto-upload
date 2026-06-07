import { randomUUID } from "node:crypto";

import { AccountExecutor } from "../executors/account-executor.js";
import { PublishExecutor } from "../executors/publish-executor.js";
import { TaskControlExecutor } from "../executors/task-control-executor.js";
import { ChildTaskRepository } from "../repositories/child-task-repository.js";
import { TaskEventRepository } from "../repositories/task-event-repository.js";
import { TaskRepository } from "../repositories/task-repository.js";
import type { AccountCheckInput, AccountLoginInput } from "../validators/account.js";
import { accountCheckSchema, accountLoginSchema } from "../validators/account.js";
import type { PublishSubmitInput } from "../validators/publish.js";
import { publishSubmitSchema } from "../validators/publish.js";

const LEGACY_TOOL_ALIAS: Record<string, string> = {
  platform_login: "account_login",
  platform_check: "account_check",
};

/**
 * 任务服务。
 * 当前先承接旧 `/mcp/tasks` 兼容入口与基础事件回放。
 */
export class TaskService {
  public constructor(
    private readonly taskRepository: TaskRepository,
    private readonly childTaskRepository: ChildTaskRepository,
    private readonly taskEventRepository: TaskEventRepository,
    private readonly accountExecutor: AccountExecutor,
    private readonly publishExecutor: PublishExecutor,
    private readonly taskControlExecutor: TaskControlExecutor,
  ) {}

  /**
   * 创建一个兼容旧协议的已受理任务。
   */
  public acceptLegacyTask(toolName: string, inputPayload: Record<string, unknown>): { task_id: string; status: "queued" } {
    const normalizedToolName = LEGACY_TOOL_ALIAS[toolName] ?? toolName;
    const taskId = `task_${randomUUID()}`;
    this.taskRepository.createTask({
      id: taskId,
      tool_name: normalizedToolName,
      task_type: normalizedToolName,
      status: "queued",
      platform: typeof inputPayload.platform === "string" ? inputPayload.platform : null,
      content_type: typeof inputPayload.content_type === "string" ? inputPayload.content_type : null,
      trigger_mode: typeof inputPayload.trigger_mode === "string" ? inputPayload.trigger_mode : null,
      input_payload: JSON.stringify(inputPayload),
    });
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.queued",
      status: "queued",
      message: "任务已受理",
      data_payload: JSON.stringify({ tool: normalizedToolName }),
    });
    return { task_id: taskId, status: "queued" };
  }

  /**
   * 创建并执行账号登录任务。
   */
  public async createAccountLoginTask(payload: unknown): Promise<{ task_id: string; status: "queued" }> {
    const input = accountLoginSchema.parse(payload);
    return await this.enqueueAccountTask("account_login", input, (taskId, parsedInput) =>
      this.accountExecutor.executeLogin(taskId, parsedInput),
    );
  }

  /**
   * 创建并执行账号校验任务。
   */
  public async createAccountCheckTask(payload: unknown): Promise<{ task_id: string; status: "queued" }> {
    const input = accountCheckSchema.parse(payload);
    return await this.enqueueAccountTask("account_check", input, (taskId, parsedInput) =>
      this.accountExecutor.executeCheck(taskId, parsedInput),
    );
  }

  /**
   * 创建并执行发布任务。
   */
  public async createPublishTask(payload: unknown): Promise<{ task_id: string; status: "queued"; child_count: number }> {
    const input = publishSubmitSchema.parse(payload);
    const taskId = `task_${randomUUID()}`;
    this.taskRepository.createTask({
      id: taskId,
      tool_name: "publish_submit",
      task_type: "publish_submit",
      status: "queued",
      platform: null,
      content_type: input.content_type,
      trigger_mode: input.trigger_mode,
      input_payload: JSON.stringify(input),
    });
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.queued",
      status: "queued",
      message: "发布任务已受理",
    });

    const result = await this.publishExecutor.execute(taskId, input);
    return { task_id: taskId, status: "queued", child_count: result.childCount };
  }

  /**
   * 取消任务。
   */
  public cancelTask(payload: unknown): { task_id: string; status: "cancelled"; cancelled_children: number } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("task cancel payload must be an object");
    }
    const taskId = (payload as { task_id?: unknown }).task_id;
    if (typeof taskId !== "string" || !taskId.trim()) {
      throw new Error("task_id is required");
    }
    return this.taskControlExecutor.cancelTask(taskId);
  }

  /**
   * 重试失败任务。
   * 当前先按原始 input_payload 重建一个新任务。
   */
  public async retryTask(payload: unknown): Promise<{ task_id: string; status: "queued" } | { task_id: string; status: "queued"; child_count: number }> {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("task retry payload must be an object");
    }
    const taskId = (payload as { task_id?: unknown }).task_id;
    if (typeof taskId !== "string" || !taskId.trim()) {
      throw new Error("task_id is required");
    }

    const task = this.taskRepository.getTask(taskId);
    if (!task) {
      throw new Error("task not found");
    }
    const inputPayload = JSON.parse(task.input_payload) as unknown;

    if (task.task_type === "account_login") {
      return await this.createAccountLoginTask(inputPayload);
    }
    if (task.task_type === "account_check") {
      return await this.createAccountCheckTask(inputPayload);
    }
    if (task.task_type === "publish_submit") {
      return await this.createPublishTask(inputPayload);
    }

    throw new Error("task retry is not supported for this task type");
  }

  /**
   * 返回任务列表。
   */
  public listTasks(): Record<string, unknown>[] {
    return this.taskRepository.listTasks().map((task) => ({
      ...task,
      input_payload: JSON.parse(task.input_payload),
      result_payload: task.result_payload ? JSON.parse(task.result_payload) : null,
      error_payload: task.error_payload ? JSON.parse(task.error_payload) : null,
    }));
  }

  /**
   * 返回任务详情。
   */
  public getTask(taskId: string): Record<string, unknown> | null {
    const task = this.taskRepository.getTask(taskId);
    if (!task) {
      return null;
    }
    return {
      ...task,
      input_payload: JSON.parse(task.input_payload),
      result_payload: task.result_payload ? JSON.parse(task.result_payload) : null,
      error_payload: task.error_payload ? JSON.parse(task.error_payload) : null,
    };
  }

  /**
   * 返回指定父任务的子任务列表。
   */
  public listChildTasks(taskId: string): Record<string, unknown>[] {
    return this.childTaskRepository.listByParentTask(taskId).map((childTask) => ({
      ...childTask,
      material_payload: JSON.parse(childTask.material_payload),
      result_payload: childTask.result_payload ? JSON.parse(childTask.result_payload) : null,
      error_payload: childTask.error_payload ? JSON.parse(childTask.error_payload) : null,
    }));
  }

  /**
   * 返回任务事件历史。
   */
  public listTaskEvents(taskId: string): Record<string, unknown>[] {
    return this.taskEventRepository.listByTask(taskId).map((event) => ({
      ...event,
      data_payload: event.data_payload ? JSON.parse(event.data_payload) : null,
    }));
  }

  /**
   * 统一创建账号类任务。
   * 账号任务当前先同步执行，后续引入真正后台执行时再替换调度方式。
   */
  private async enqueueAccountTask<TInput extends AccountLoginInput | AccountCheckInput>(
    toolName: "account_login" | "account_check",
    input: TInput,
    execute: (taskId: string, parsedInput: TInput) => Promise<void>,
  ): Promise<{ task_id: string; status: "queued" }> {
    const taskId = `task_${randomUUID()}`;
    this.taskRepository.createTask({
      id: taskId,
      tool_name: toolName,
      task_type: toolName,
      status: "queued",
      platform: input.platform,
      input_payload: JSON.stringify(input),
    });
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.queued",
      status: "queued",
      message: `${toolName} 任务已受理`,
    });
    await execute(taskId, input);
    return { task_id: taskId, status: "queued" };
  }
}
