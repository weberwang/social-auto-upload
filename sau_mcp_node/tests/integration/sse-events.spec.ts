import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { buildApp } from "../../src/app.js";
import { openDatabase } from "../../src/db/connection.js";
import { runMigrations } from "../../src/db/migrator.js";
import { TaskEventRepository } from "../../src/repositories/task-event-repository.js";
import { TaskRepository } from "../../src/repositories/task-repository.js";

const createdDirectories = new Set<string>();

afterEach(() => {
  for (const directory of createdDirectories) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
  createdDirectories.clear();
});

/**
 * 创建隔离工作区。
 * SSE 回放测试会提前插入任务和事件，再通过 HTTP 验证顺序。
 */
function createTempWorkspace(): { baseDir: string; databasePath: string } {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-sse-"));
  createdDirectories.add(baseDir);
  return {
    baseDir,
    databasePath: path.join(baseDir, "db", "database.db"),
  };
}

describe("task event replay", () => {
  it("replays queued running succeeded in order", async () => {
    const workspace = createTempWorkspace();
    const database = openDatabase(workspace.databasePath);
    runMigrations(database);

    const taskRepository = new TaskRepository(database);
    const taskEventRepository = new TaskEventRepository(database);
    taskRepository.createTask({
      id: "task_demo",
      tool_name: "account_login",
      task_type: "account_login",
      status: "succeeded",
      platform: "douyin",
      input_payload: JSON.stringify({ platform: "douyin", account_name: "demo" }),
    });
    taskEventRepository.appendEvent({
      task_id: "task_demo",
      event_type: "task.queued",
      status: "queued",
      message: "任务已受理",
    });
    taskEventRepository.appendEvent({
      task_id: "task_demo",
      event_type: "task.running",
      status: "running",
      message: "任务执行中",
    });
    taskEventRepository.appendEvent({
      task_id: "task_demo",
      event_type: "task.succeeded",
      status: "succeeded",
      message: "任务执行成功",
    });
    database.close();

    const app = buildApp(workspace);
    const response = await app.inject({
      method: "GET",
      url: "/mcp/tasks/task_demo/events",
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers["content-type"]).toContain("text/event-stream");
    expect(response.body).toContain("event: task.queued");
    expect(response.body).toContain("event: task.running");
    expect(response.body).toContain("event: task.succeeded");

    await app.close();
  });
});
