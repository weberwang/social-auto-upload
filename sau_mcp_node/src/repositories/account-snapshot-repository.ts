import type Database from "better-sqlite3";

export type UpsertAccountSnapshotInput = {
  platform: string;
  account_name: string;
  account_file: string;
  last_check_status: string;
  last_check_at: string;
  last_error_payload?: string | null;
};

/**
 * 账号快照仓储。
 * 用于把最近一次校验结果回写到 SQLite，供账号列表展示复用。
 */
export class AccountSnapshotRepository {
  public constructor(private readonly database: Database.Database) {}

  /**
   * 写入或更新账号最近一次校验结果。
   */
  public upsertSnapshot(input: UpsertAccountSnapshotInput): void {
    this.database
      .prepare(
        `
          INSERT INTO mcp_accounts_snapshot (
            platform,
            account_name,
            account_file,
            last_check_status,
            last_check_at,
            last_error_payload
          )
          VALUES (?, ?, ?, ?, ?, ?)
          ON CONFLICT(platform, account_name)
          DO UPDATE SET
            account_file = excluded.account_file,
            last_check_status = excluded.last_check_status,
            last_check_at = excluded.last_check_at,
            last_error_payload = excluded.last_error_payload,
            updated_at = CURRENT_TIMESTAMP
        `,
      )
      .run(
        input.platform,
        input.account_name,
        input.account_file,
        input.last_check_status,
        input.last_check_at,
        input.last_error_payload ?? null,
      );
  }
}
