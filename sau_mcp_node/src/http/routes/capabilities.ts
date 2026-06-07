import type { FastifyInstance } from "fastify";

import { CapabilityService } from "../../services/capability-service.js";

/**
 * 注册能力查询路由。
 */
export function registerCapabilityRoutes(app: FastifyInstance): void {
  const capabilityService = new CapabilityService();

  app.get("/mcp/capabilities", async () => capabilityService.getCapabilities());
}
