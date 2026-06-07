import type { FastifyInstance } from "fastify";

import { TaskService } from "../../services/task-service.js";

/**
 * 注册任务查询和旧兼容入口。
 */
export function registerTaskRoutes(app: FastifyInstance, taskService: TaskService): void {
  app.get("/mcp/tasks", async () => ({
    items: taskService.listTasks(),
  }));

  app.get<{ Params: { taskId: string } }>("/mcp/tasks/:taskId", async (request, reply) => {
    const task = taskService.getTask(request.params.taskId);
    if (!task) {
      return reply.code(404).send({ error: "task not found" });
    }
    return task;
  });

  app.get<{ Params: { taskId: string } }>("/mcp/tasks/:taskId/children", async (request) => ({
    items: taskService.listChildTasks(request.params.taskId),
  }));

  app.post<{ Body: { tool?: unknown; input?: unknown } }>("/mcp/tasks", async (request, reply) => {
    if (!request.body || typeof request.body !== "object") {
      return reply.code(400).send({ error: "request body must be a non-empty JSON object" });
    }
    if (typeof request.body.tool !== "string" || !request.body.tool.trim()) {
      return reply.code(400).send({ error: "tool is required" });
    }
    if (!request.body.input || typeof request.body.input !== "object" || Array.isArray(request.body.input)) {
      return reply.code(400).send({ error: "input must be an object" });
    }

    return reply.code(202).send(taskService.acceptLegacyTask(request.body.tool, request.body.input as Record<string, unknown>));
  });
}
