import { randomUUID } from "node:crypto";

import type { PublishNoteBridgeInput, PublishVideoBridgeInput } from "../bridges/python-publish-bridge.js";
import { runPublishNoteBridge, runPublishVideoBridge } from "../bridges/python-publish-bridge.js";
import type { ChildTaskRepository, CreateChildTaskInput } from "../repositories/child-task-repository.js";
import type { TaskEventRepository } from "../repositories/task-event-repository.js";
import type { TaskRepository } from "../repositories/task-repository.js";
import type { PublishSubmitInput } from "../validators/publish.js";

function nowIso(): string {
  return new Date().toISOString();
}

type PublishChildUnit = {
  id: string;
  parent_task_id: string;
  platform: string;
  account_name: string;
  content_type: "video" | "image_text";
  material_payload: string;
};

/**
 * 发布任务执行器。
 * 当前先保守串行执行，优先保证同账号不并发和父子任务状态正确。
 */
export class PublishExecutor {
  public constructor(
    private readonly taskRepository: TaskRepository,
    private readonly childTaskRepository: ChildTaskRepository,
    private readonly taskEventRepository: TaskEventRepository,
  ) {}

  /**
   * 展开并执行父任务。
   */
  public async execute(taskId: string, input: PublishSubmitInput): Promise<{ childCount: number }> {
    const childUnits = this.buildChildUnits(taskId, input);
    const childInputs: CreateChildTaskInput[] = childUnits.map((unit) => ({
      ...unit,
      status: "queued",
    }));

    this.childTaskRepository.createMany(childInputs);
    this.taskRepository.updateProgress(taskId, childInputs.length, 0, 0);
    this.taskRepository.markRunning(taskId, nowIso());
    this.taskEventRepository.appendEvent({
      task_id: taskId,
      event_type: "task.running",
      status: "running",
      message: "发布任务执行中",
      data_payload: JSON.stringify({ child_count: childInputs.length }),
    });

    let successCount = 0;
    let failedCount = 0;

    for (const childUnit of childUnits) {
      const startedAt = nowIso();
      this.childTaskRepository.markRunning(childUnit.id, startedAt);
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        child_task_id: childUnit.id,
        event_type: "child_task.running",
        status: "running",
        message: `${childUnit.platform} 子任务执行中`,
      });

      try {
        const materialPayload = JSON.parse(childUnit.material_payload) as Record<string, unknown>;
        const result =
          childUnit.content_type === "video"
            ? await runPublishVideoBridge(this.toVideoBridgeInput(childUnit.platform, childUnit.account_name, input, materialPayload))
            : await runPublishNoteBridge(this.toNoteBridgeInput(childUnit.platform, childUnit.account_name, input, materialPayload));

        if (!result.success) {
          throw new Error(result.error?.message ?? "publish failed");
        }

        successCount += 1;
        this.childTaskRepository.markSucceeded(childUnit.id, JSON.stringify(result), nowIso());
        this.taskEventRepository.appendEvent({
          task_id: taskId,
          child_task_id: childUnit.id,
          event_type: "child_task.succeeded",
          status: "succeeded",
          message: `${childUnit.platform} 子任务执行成功`,
          data_payload: JSON.stringify(result),
        });
      } catch (error) {
        failedCount += 1;
        const errorPayload = {
          code: "publish_child_failed",
          message: error instanceof Error ? error.message : String(error),
        };
        this.childTaskRepository.markFailed(childUnit.id, JSON.stringify(errorPayload), nowIso());
        this.taskEventRepository.appendEvent({
          task_id: taskId,
          child_task_id: childUnit.id,
          event_type: "child_task.failed",
          status: "failed",
          message: `${childUnit.platform} 子任务执行失败`,
          data_payload: JSON.stringify(errorPayload),
        });
      }

      this.taskRepository.updateProgress(taskId, childUnits.length, successCount, failedCount);
    }

    const summaryPayload = JSON.stringify({
      summary: {
        total_count: childUnits.length,
        success_count: successCount,
        failed_count: failedCount,
        cancelled_count: 0,
      },
    });

    if (failedCount > 0) {
      this.taskRepository.markFailed({
        taskId,
        errorPayload: summaryPayload,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.failed",
        status: "failed",
        message: "发布任务存在失败子任务",
        data_payload: summaryPayload,
      });
    } else {
      this.taskRepository.markSucceeded({
        taskId,
        resultPayload: summaryPayload,
        finishedAt: nowIso(),
      });
      this.taskEventRepository.appendEvent({
        task_id: taskId,
        event_type: "task.succeeded",
        status: "succeeded",
        message: "发布任务执行成功",
        data_payload: summaryPayload,
      });
    }

    return { childCount: childUnits.length };
  }

  /**
   * 把请求按 `平台 x 账号 x 素材单元` 展开。
   * 图文多图保持为单个素材单元，不拆成单图。
   */
  private buildChildUnits(taskId: string, input: PublishSubmitInput): PublishChildUnit[] {
    return input.targets.flatMap((target: PublishSubmitInput["targets"][number]) =>
      input.materials.map((material: PublishSubmitInput["materials"][number]) => ({
        id: `child_${randomUUID()}`,
        parent_task_id: taskId,
        platform: target.platform,
        account_name: target.account_name,
        content_type: input.content_type,
        material_payload: JSON.stringify(material),
      })),
    );
  }

  /**
   * 组装视频 bridge 输入。
   */
  private toVideoBridgeInput(
    platform: string,
    accountName: string,
    input: PublishSubmitInput,
    materialPayload: Record<string, unknown>,
  ): PublishVideoBridgeInput {
    return {
      platform,
      account_name: accountName,
      file_path: String(materialPayload.file_path),
      title: input.metadata.title,
      description: input.metadata.desc,
      tags: input.metadata.tags,
      tid: input.metadata.tid,
    };
  }

  /**
   * 组装图文 bridge 输入。
   */
  private toNoteBridgeInput(
    platform: string,
    accountName: string,
    input: PublishSubmitInput,
    materialPayload: Record<string, unknown>,
  ): PublishNoteBridgeInput {
    const files = Array.isArray(materialPayload.files) ? materialPayload.files.map((item) => String(item)) : [];
    return {
      platform,
      account_name: accountName,
      image_files: files,
      title: input.metadata.title,
      note: input.metadata.note ?? "",
      tags: input.metadata.tags,
    };
  }
}
