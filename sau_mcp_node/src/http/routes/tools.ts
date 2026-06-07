import type { FastifyInstance } from "fastify";

import type { DraftService } from "../../services/draft-service.js";
import type { ScheduleService } from "../../services/schedule-service.js";
import type { TaskService } from "../../services/task-service.js";

/**
 * 预留新的领域工具入口。
 * Task 5 先把路由占住，具体工具执行在后续任务接入。
 */
export function registerToolRoutes(
  app: FastifyInstance,
  taskService: TaskService,
  draftService: DraftService,
  scheduleService: ScheduleService,
): void {
  app.post<{ Params: { toolName: string }; Body: unknown }>("/mcp/tools/:toolName", async (request, reply) => {
    try {
      if (request.params.toolName === "account_login") {
        return reply.code(202).send(await taskService.createAccountLoginTask(request.body));
      }
      if (request.params.toolName === "account_check") {
        return reply.code(202).send(await taskService.createAccountCheckTask(request.body));
      }
      if (request.params.toolName === "publish_submit") {
        return reply.code(202).send(await taskService.createPublishTask(request.body));
      }
      if (request.params.toolName === "draft_save") {
        return reply.send(draftService.saveDraft(request.body));
      }
      if (request.params.toolName === "draft_delete") {
        return reply.send(draftService.deleteDraft(request.body));
      }
      if (request.params.toolName === "schedule_create") {
        return reply.send(scheduleService.createSchedule(request.body));
      }
      if (request.params.toolName === "schedule_update") {
        return reply.send(scheduleService.updateSchedule(request.body));
      }
      if (request.params.toolName === "schedule_delete") {
        return reply.send(scheduleService.deleteSchedule(request.body));
      }
      if (request.params.toolName === "task_cancel") {
        return reply.send(taskService.cancelTask(request.body));
      }
      if (request.params.toolName === "task_retry") {
        return reply.code(202).send(await taskService.retryTask(request.body));
      }
      return reply.code(501).send({ error: "tool invocation is not implemented yet" });
    } catch (error) {
      return reply.code(400).send({
        error: error instanceof Error ? error.message : String(error),
      });
    }
  });
}
