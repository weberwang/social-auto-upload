import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import Database from "better-sqlite3";
import { afterEach, describe, expect, it } from "vitest";

import { openDatabase } from "../../src/db/connection.js";
import { runMigrations } from "../../src/db/migrator.js";
import { DraftRepository } from "../../src/repositories/draft-repository.js";

const createdDirectories = new Set<string>();

afterEach(() => {
  for (const directory of createdDirectories) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
  createdDirectories.clear();
});

/**
 * 创建隔离的测试数据库目录。
 * 草稿导入测试会直接在这里构造旧表和新表，避免污染真实工作区。
 */
function createTempDatabasePath(): string {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-draft-compat-"));
  createdDirectories.add(directory);
  return path.join(directory, "database.db");
}

describe("draft migration compatibility", () => {
  it("imports legacy publish_drafts rows into mcp_publish_drafts", () => {
    const databasePath = createTempDatabasePath();
    const legacyDatabase = new Database(databasePath);
    legacyDatabase.exec(`
      CREATE TABLE publish_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);
    legacyDatabase
      .prepare(
        `
          INSERT INTO publish_drafts (name, payload)
          VALUES (?, ?)
        `,
      )
      .run("旧草稿", JSON.stringify({ activeTab: "tab1" }));
    legacyDatabase.close();

    const database = openDatabase(databasePath);
    runMigrations(database);
    const repository = new DraftRepository(database);

    const firstResult = repository.importLegacyDrafts();
    const secondResult = repository.importLegacyDrafts();
    const importedRow = database
      .prepare<[], { readonly legacy_draft_id: number; readonly name: string; readonly workspace_payload: string }>(
        `
          SELECT legacy_draft_id, name, workspace_payload
          FROM mcp_publish_drafts
        `,
      )
      .get();

    expect(firstResult.importedCount).toBe(1);
    expect(secondResult.importedCount).toBe(0);
    expect(importedRow).toEqual({
      legacy_draft_id: 1,
      name: "旧草稿",
      workspace_payload: JSON.stringify({ activeTab: "tab1" }),
    });

    database.close();
  });
});
