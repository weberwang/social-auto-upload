import type Database from "better-sqlite3";

type SqliteDatabase = InstanceType<typeof Database>;

/**
 * 旧草稿导入结果。
 * 让调用方能明确知道这次导入到底插入了多少条记录。
 */
export type LegacyDraftImportResult = {
  importedCount: number;
};

/**
 * MCP 草稿仓储。
 * Task 2 只先承接旧草稿导入，后续 CRUD 在后续任务中补齐。
 */
export class DraftRepository {
  public constructor(private readonly database: SqliteDatabase) {}

  /**
   * 导入旧 `publish_drafts` 到新版 MCP 草稿表。
   * 通过 `legacy_draft_id` 去重，保证重复执行也不会二次导入。
   */
  public importLegacyDrafts(): LegacyDraftImportResult {
    const legacyTableExists = this.database
      .prepare(
        `
          SELECT name
          FROM sqlite_master
          WHERE type = 'table' AND name = 'publish_drafts'
        `,
      )
      .get();

    if (!legacyTableExists) {
      return { importedCount: 0 };
    }

    const result = this.database
      .prepare(
        `
          INSERT INTO mcp_publish_drafts (
            legacy_draft_id,
            name,
            workspace_payload,
            created_at,
            updated_at
          )
          SELECT
            pd.id,
            pd.name,
            pd.payload,
            pd.created_at,
            pd.updated_at
          FROM publish_drafts AS pd
          WHERE NOT EXISTS (
            SELECT 1
            FROM mcp_publish_drafts AS mpd
            WHERE mpd.legacy_draft_id = pd.id
          )
        `,
      )
      .run();

    return { importedCount: result.changes };
  }
}
