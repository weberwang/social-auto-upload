import type { FastifyInstance } from "fastify";

import { DraftService } from "../../services/draft-service.js";

/**
 * 注册草稿查询路由。
 */
export function registerDraftRoutes(app: FastifyInstance, draftService: DraftService): void {
  app.get("/mcp/drafts", async () => ({
    items: draftService.listDrafts(),
  }));

  app.get<{ Params: { draftId: string } }>("/mcp/drafts/:draftId", async (request, reply) => {
    const draftId = Number.parseInt(request.params.draftId, 10);
    if (!Number.isInteger(draftId) || draftId <= 0) {
      return reply.code(400).send({ error: "draft_id must be a positive integer" });
    }

    const draft = draftService.getDraft(draftId);
    if (!draft) {
      return reply.code(404).send({ error: "draft not found" });
    }

    return draft;
  });
}
