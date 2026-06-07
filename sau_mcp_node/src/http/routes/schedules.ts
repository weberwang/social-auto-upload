import type { FastifyInstance } from "fastify";

import { ScheduleService } from "../../services/schedule-service.js";

/**
 * 注册定时计划查询路由。
 */
export function registerScheduleRoutes(app: FastifyInstance, scheduleService: ScheduleService): void {
  app.get("/mcp/schedules", async () => ({
    items: scheduleService.listSchedules(),
  }));

  app.get<{ Params: { scheduleId: string } }>("/mcp/schedules/:scheduleId", async (request, reply) => {
    const schedule = scheduleService.getSchedule(request.params.scheduleId);
    if (!schedule) {
      return reply.code(404).send({ error: "schedule not found" });
    }
    return schedule;
  });
}
