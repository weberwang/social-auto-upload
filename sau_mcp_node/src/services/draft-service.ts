import type Database from "better-sqlite3";

export type DraftListItem = {
  id: number;
  legacy_draft_id: number | null;
  name: string;
  created_at: string;
  updated_at: string;
};

/**
 * 草稿查询服务。
 * Task 4 先提供列表与详情读取，写接口在后续任务中补齐。
 */
export class DraftService {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 返回 MCP 草稿列表。
   */
  public listDrafts(): DraftListItem[] {
    return this.database
      .prepare<[], DraftListItem>(
        `
          SELECT id, legacy_draft_id, name, created_at, updated_at
          FROM mcp_publish_drafts
          ORDER BY datetime(updated_at) DESC, id DESC
        `,
      )
      .all();
  }

  /**
   * 返回单个草稿详情。
   */
  public getDraft(draftId: number): Record<string, unknown> | null {
    const row = this.database
      .prepare<[number], { id: number; legacy_draft_id: number | null; name: string; workspace_payload: string; created_at: string; updated_at: string }>(
        `
          SELECT id, legacy_draft_id, name, workspace_payload, created_at, updated_at
          FROM mcp_publish_drafts
          WHERE id = ?
        `,
      )
      .get(draftId);

    if (!row) {
      return null;
    }

    return {
      id: row.id,
      legacy_draft_id: row.legacy_draft_id,
      name: row.name,
      workspace: JSON.parse(row.workspace_payload),
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }

  /**
   * 保存草稿。
   * 先兼容“新建草稿”和“覆盖现有草稿”两种模式。
   */
  public saveDraft(payload: unknown): { draft_id: number; status: "saved" } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("draft payload must be an object");
    }

    const draft = payload as {
      id?: unknown;
      name?: unknown;
      workspace?: unknown;
      metadata?: unknown;
      schedule?: unknown;
    };

    if (typeof draft.name !== "string" || !draft.name.trim()) {
      throw new Error("draft name is required");
    }
    if (!draft.workspace || typeof draft.workspace !== "object" || Array.isArray(draft.workspace)) {
      throw new Error("draft workspace must be an object");
    }

    const metadataPayload = draft.metadata && typeof draft.metadata === "object" ? JSON.stringify(draft.metadata) : null;
    const schedulePayload = draft.schedule && typeof draft.schedule === "object" ? JSON.stringify(draft.schedule) : null;
    const workspacePayload = JSON.stringify(draft.workspace);

    if (draft.id == null) {
      const result = this.database
        .prepare(
          `
            INSERT INTO mcp_publish_drafts (
              name,
              metadata_payload,
              schedule_payload,
              workspace_payload
            )
            VALUES (?, ?, ?, ?)
          `,
        )
        .run(draft.name.trim(), metadataPayload, schedulePayload, workspacePayload);
      return { draft_id: Number(result.lastInsertRowid), status: "saved" };
    }

    const draftId = Number.parseInt(String(draft.id), 10);
    if (!Number.isInteger(draftId) || draftId <= 0) {
      throw new Error("draft id must be a positive integer");
    }

    const result = this.database
      .prepare(
        `
          UPDATE mcp_publish_drafts
          SET name = ?,
              metadata_payload = ?,
              schedule_payload = ?,
              workspace_payload = ?,
              updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `,
      )
      .run(draft.name.trim(), metadataPayload, schedulePayload, workspacePayload, draftId);

    if (result.changes === 0) {
      throw new Error("draft not found");
    }

    return { draft_id: draftId, status: "saved" };
  }

  /**
   * 删除草稿。
   */
  public deleteDraft(payload: unknown): { draft_id: number; status: "deleted" } {
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("draft delete payload must be an object");
    }
    const draftId = Number.parseInt(String((payload as { draft_id?: unknown }).draft_id), 10);
    if (!Number.isInteger(draftId) || draftId <= 0) {
      throw new Error("draft_id must be a positive integer");
    }

    const result = this.database
      .prepare(
        `
          DELETE FROM mcp_publish_drafts
          WHERE id = ?
        `,
      )
      .run(draftId);

    if (result.changes === 0) {
      throw new Error("draft not found");
    }

    return { draft_id: draftId, status: "deleted" };
  }
}
