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
 * 查询路由测试会在这里启动 Node MCP，避免污染真实仓库数据库。
 */
function createTempWorkspace(): { baseDir: string; databasePath: string } {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-query-routes-"));
  createdDirectories.add(baseDir);
  return {
    baseDir,
    databasePath: path.join(baseDir, "db", "database.db"),
  };
}

describe("query routes", () => {
  it("returns health metadata and tencent in capabilities", async () => {
    const workspace = createTempWorkspace();
    const app = buildApp(workspace);

    const health = await app.inject({ method: "GET", url: "/mcp/health" });
    const capabilities = await app.inject({ method: "GET", url: "/mcp/capabilities" });

    expect(health.statusCode).toBe(200);
    expect(health.json()).toMatchObject({
      status: "ok",
      service: "social-auto-upload-mcp",
      queue_size: 0,
    });
    expect(capabilities.statusCode).toBe(200);
    expect(capabilities.json().platforms).toContain("tencent");
    expect(capabilities.json().tools).toContain("publish_submit");

    await app.close();
  });
});
