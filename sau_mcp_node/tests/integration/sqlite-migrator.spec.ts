import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { openDatabase } from "../../src/db/connection.js";
import { runMigrations } from "../../src/db/migrator.js";

const createdDirectories = new Set<string>();

afterEach(() => {
  for (const directory of createdDirectories) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
  createdDirectories.clear();
});

/**
 * 创建迁移测试所需的临时数据库路径。
 * 每个用例单独建库，避免表结构检测互相污染。
 */
function createTempDatabasePath(): string {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-migrator-"));
  createdDirectories.add(directory);
  return path.join(directory, "database.db");
}

describe("sqlite migrator", () => {
  it("creates task, child task, event, draft, schedule and account snapshot tables", () => {
    const database = openDatabase(createTempDatabasePath());
    runMigrations(database);

    const rows = database
      .prepare<[], { readonly name: string }>(
        `
          SELECT name
          FROM sqlite_master
          WHERE type = 'table'
        `,
      )
      .all();
    const tables = rows.map((row) => row.name);

    expect(tables).toContain("mcp_tasks");
    expect(tables).toContain("mcp_task_children");
    expect(tables).toContain("mcp_task_events");
    expect(tables).toContain("mcp_publish_drafts");
    expect(tables).toContain("mcp_schedules");
    expect(tables).toContain("mcp_accounts_snapshot");
    expect(tables).toContain("mcp_schema_migrations");

    database.close();
  });
});
