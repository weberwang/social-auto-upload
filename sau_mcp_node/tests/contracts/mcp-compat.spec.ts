import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { buildApp } from "../../src/app.js";

const createdDirectories = new Set<string>();

afterEach(() => {
  for (const directory of createdDirectories) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
  createdDirectories.clear();
});

/**
 * 创建隔离工作区。
 * 兼容测试会在这里创建数据库和 app，避免污染真实仓库。
 */
function createTempWorkspace(): { baseDir: string; databasePath: string } {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-compat-"));
  createdDirectories.add(baseDir);
  return {
    baseDir,
    databasePath: path.join(baseDir, "db", "database.db"),
  };
}

describe("mcp compatibility contract", () => {
  it("accepts legacy task payload and returns queued task metadata", async () => {
    const workspace = createTempWorkspace();
    const app = buildApp(workspace);

    const response = await app.inject({
      method: "POST",
      url: "/mcp/tasks",
      payload: {
        tool: "platform_login",
        input: {
          platform: "douyin",
          account_name: "demo",
          headless: true,
        },
      },
    });

    expect(response.statusCode).toBe(202);
    expect(response.json()).toMatchObject({
      status: "queued",
    });
    expect(response.json().task_id).toMatch(/^task_/);

    await app.close();
  });
});
