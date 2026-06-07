import type { FastifyInstance } from "fastify";

import { AccountService } from "../../services/account-service.js";

/**
 * 注册账号查询路由。
 */
export function registerAccountRoutes(app: FastifyInstance, accountService: AccountService): void {
  app.get("/mcp/accounts", async () => ({
    accounts: accountService.listAccounts(),
  }));
}
