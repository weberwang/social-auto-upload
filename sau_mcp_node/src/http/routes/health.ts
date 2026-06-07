import type { FastifyInstance } from "fastify";

/**
 * 注册健康检查路由。
 */
export function registerHealthRoutes(app: FastifyInstance): void {
  app.get("/mcp/health", async () => ({
    status: "ok",
    service: "social-auto-upload-mcp",
    queue_size: 0,
  }));
}
