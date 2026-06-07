import type { FastifyInstance } from "fastify";

import { TaskService } from "../../services/task-service.js";

/**
 * 注册任务事件回放路由。
 * Task 5 先提供历史回放，长轮询和持续推流在后续任务接入。
 */
export function registerTaskEventRoutes(app: FastifyInstance, taskService: TaskService): void {
  app.get<{ Params: { taskId: string } }>("/mcp/tasks/:taskId/events", async (request, reply) => {
    const task = taskService.getTask(request.params.taskId);
    if (!task) {
      return reply.code(404).send({ error: "task not found" });
    }

    const events = taskService.listTaskEvents(request.params.taskId);
    const payload = events
      .map((event) => `event: ${String(event.event_type)}\ndata: ${JSON.stringify(event)}\n`)
      .join("\n");

    reply.header("Content-Type", "text/event-stream");
    reply.header("Cache-Control", "no-cache");
    return reply.send(payload ? `${payload}\n` : "");
  });
}
