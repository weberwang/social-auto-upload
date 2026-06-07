import fs from "node:fs";
import path from "node:path";

import type Database from "better-sqlite3";

import type { PlatformName } from "../shared/platforms.js";

type AccountSnapshotRow = {
  platform: string;
  account_name: string;
  account_file: string;
  last_check_status: string | null;
  last_check_at: string | null;
};

export type AccountSummary = {
  account_name: string;
  account_file: string;
  last_check_status: string | null;
  last_check_at: string | null;
};

/**
 * 账号查询服务。
 * 先按 cookies 目录枚举账号文件，再拼上最近一次快照信息。
 */
export class AccountService {
  public constructor(
    private readonly database: Database.Database,
    private readonly baseDir: string,
  ) {}

  /**
   * 返回按平台分组的账号列表。
   */
  public listAccounts(): Record<string, AccountSummary[]> {
    const cookiesDir = path.join(this.baseDir, "cookies");
    const groupedAccounts = new Map<string, AccountSummary[]>();
    const snapshotByKey = new Map<string, AccountSnapshotRow>();
    const snapshotRows = this.database
      .prepare<[], AccountSnapshotRow>(
        `
          SELECT platform, account_name, account_file, last_check_status, last_check_at
          FROM mcp_accounts_snapshot
        `,
      )
      .all();

    for (const row of snapshotRows) {
      snapshotByKey.set(`${row.platform}:${row.account_name}`, row);
    }

    if (!fs.existsSync(cookiesDir)) {
      return {};
    }

    for (const entry of fs.readdirSync(cookiesDir, { withFileTypes: true })) {
      if (!entry.isFile() || !entry.name.endsWith(".json")) {
        continue;
      }
      const parsed = this.parseAccountFileName(entry.name);
      if (!parsed) {
        continue;
      }
      const snapshot = snapshotByKey.get(`${parsed.platform}:${parsed.accountName}`);
      const items = groupedAccounts.get(parsed.platform) ?? [];
      items.push({
        account_name: parsed.accountName,
        account_file: path.join("cookies", entry.name).replaceAll("\\", "/"),
        last_check_status: snapshot?.last_check_status ?? null,
        last_check_at: snapshot?.last_check_at ?? null,
      });
      groupedAccounts.set(parsed.platform, items);
    }

    return Object.fromEntries(
      [...groupedAccounts.entries()].map(([platform, items]) => [
        platform,
        items.sort((left, right) => left.account_name.localeCompare(right.account_name)),
      ]),
    );
  }

  /**
   * 解析账号文件名。
   * 只接受 `platform_account.json` 这一主线命名，避免把其它文件误判成账号。
   */
  private parseAccountFileName(
    fileName: string,
  ): { platform: PlatformName; accountName: string } | null {
    const withoutExtension = fileName.slice(0, -".json".length);
    const separatorIndex = withoutExtension.indexOf("_");
    if (separatorIndex <= 0) {
      return null;
    }
    const platform = withoutExtension.slice(0, separatorIndex);
    const accountName = withoutExtension.slice(separatorIndex + 1);
    if (!["douyin", "kuaishou", "xiaohongshu", "bilibili", "tencent"].includes(platform) || !accountName) {
      return null;
    }
    return { platform: platform as PlatformName, accountName };
  }
}
