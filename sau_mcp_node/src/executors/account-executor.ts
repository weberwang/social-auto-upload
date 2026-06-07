import type { AccountCheckBridgeInput, AccountLoginBridgeInput } from "../bridges/python-account-bridge.js";
import { runAccountCheckBridge, runAccountLoginBridge } from "../bridges/python-account-bridge.js";
import type { AccountSnapshotRepository } from "../repositories/account-snapshot-repository.js";
import type { TaskEventRepository } from "../repositories/task-event-repository.js";
import type { TaskRepository } from "../repositories/task-repository.js";
import type { AccountCheckInput, AccountLoginInput } from "../validators/account.js";

function nowIso(): string {
  return new Date().toISOString();
}

/**
 * 账号任务执行器。
 * 当前负责登录与校验两类长任务的状态推进和 bridge 调用。
 */
export class AccountExecutor {
  public constructor(
    private readonly taskRepository: TaskRepository,
    private readonly taskEventRepository: TaskEventRepository,
    private readonly accountSnapshotRepository: AccountSnapshotRepository,
  ) {}

  /**
   * 执行账号登录任务。
   */
  public async executeLogin(taskId: string, input: AccountLoginInput): Promise<void> {
    const startedAt = nowIso();
    this.taskRepository.markRunning(taskId, startedAt);
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.running",
      status: "running",
      message: "账号登录任务执行中",
    });

    try {
      const result = await runAccountLoginBridge(input satisfies AccountLoginBridgeInput);
      if (!result.success) {
        throw new Error(result.error?.message ?? "account login failed");
      }

      this.taskRepository.markSucceeded({
        taskId,
        resultPayload: JSON.stringify(result),
        startedAt,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.succeeded",
        status: "succeeded",
        message: "账号登录任务执行成功",
        data_payload: JSON.stringify(result),
      });
    } catch (error) {
      const errorPayload = {
        code: "account_login_failed",
        message: error instanceof Error ? error.message : String(error),
      };
      this.taskRepository.markFailed({
        taskId,
        errorPayload: JSON.stringify(errorPayload),
        startedAt,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.failed",
        status: "failed",
        message: "账号登录任务执行失败",
        data_payload: JSON.stringify(errorPayload),
      });
    }
  }

  /**
   * 执行账号校验任务。
   */
  public async executeCheck(taskId: string, input: AccountCheckInput): Promise<void> {
    const startedAt = nowIso();
    this.taskRepository.markRunning(taskId, startedAt);
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.running",
      status: "running",
      message: "账号校验任务执行中",
    });

    try {
      const result = await runAccountCheckBridge(input satisfies AccountCheckBridgeInput);
      if (!result.success) {
        throw new Error(result.error?.message ?? "account check failed");
      }

      this.accountSnapshotRepository.upsertSnapshot({
        platform: input.platform,
        account_name: input.account_name,
        account_file: `cookies/${input.platform}_${input.account_name}.json`,
        last_check_status: result.data?.valid ? "valid" : "invalid",
        last_check_at: nowIso(),
      });

      this.taskRepository.markSucceeded({
        taskId,
        resultPayload: JSON.stringify(result),
        startedAt,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.succeeded",
        status: "succeeded",
        message: "账号校验任务执行成功",
        data_payload: JSON.stringify(result),
      });
    } catch (error) {
      const errorPayload = {
        code: "account_check_failed",
        message: error instanceof Error ? error.message : String(error),
      };
      this.accountSnapshotRepository.upsertSnapshot({
        platform: input.platform,
        account_name: input.account_name,
        account_file: `cookies/${input.platform}_${input.account_name}.json`,
        last_check_status: "error",
        last_check_at: nowIso(),
        last_error_payload: JSON.stringify(errorPayload),
      });
      this.taskRepository.markFailed({
        taskId,
        errorPayload: JSON.stringify(errorPayload),
        startedAt,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.failed",
        status: "failed",
        message: "账号校验任务执行失败",
        data_payload: JSON.stringify(errorPayload),
      });
    }
  }
}
