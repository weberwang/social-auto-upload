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
 * 创建带 cookie 文件的隔离工作区。
 * 账号校验与发布请求都会基于这里的 cookies 路径运行。
 */
function createTempWorkspace(): { baseDir: string; databasePath: string } {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-task-flow-"));
  createdDirectories.add(baseDir);
  fs.mkdirSync(path.join(baseDir, "cookies"), { recursive: true });
  fs.writeFileSync(path.join(baseDir, "cookies", "douyin_demo.json"), "{}");
  fs.writeFileSync(path.join(baseDir, "cookies", "kuaishou_demo2.json"), "{}");
  return {
    baseDir,
    databasePath: path.join(baseDir, "db", "database.db"),
  };
}

describe("task flow", () => {
  it("creates one child task per platform-account-material unit", async () => {
    const workspace = createTempWorkspace();
    const app = buildApp(workspace);

    const response = await app.inject({
      method: "POST",
      url: "/mcp/tools/publish_submit",
      payload: {
        trigger_mode: "immediate",
        content_type: "image_text",
        targets: [
          { platform: "douyin", account_name: "demo" },
          { platform: "kuaishou", account_name: "demo2" },
        ],
        materials: [{ type: "image_text", files: ["1.png", "2.png"] }],
        metadata: { title: "图文标题", note: "图文正文", tags: ["旅行"] },
      },
    });

    expect(response.statusCode).toBe(202);
    expect(response.json().child_count).toBe(2);

    const taskId = response.json().task_id as string;
    const childResponse = await app.inject({
      method: "GET",
      url: `/mcp/tasks/${taskId}/children`,
    });

    expect(childResponse.statusCode).toBe(200);
    expect(childResponse.json().items).toHaveLength(2);

    await app.close();
  });
});
