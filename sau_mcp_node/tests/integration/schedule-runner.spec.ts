import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { buildApp } from "../../src/app.js";
import { openDatabase } from "../../src/db/connection.js";
import { runMigrations } from "../../src/db/migrator.js";
import { ScheduleRepository } from "../../src/repositories/schedule-repository.js";
import { AccountSnapshotRepository } from "../../src/repositories/account-snapshot-repository.js";
import { ChildTaskRepository } from "../../src/repositories/child-task-repository.js";
import { TaskEventRepository } from "../../src/repositories/task-event-repository.js";
import { TaskRepository } from "../../src/repositories/task-repository.js";
import { TaskControlExecutor } from "../../src/executors/task-control-executor.js";
import { ScheduleRunner } from "../../src/scheduler/schedule-runner.js";
import { TaskService } from "../../src/services/task-service.js";
import { AccountExecutor } from "../../src/executors/account-executor.js";
import { PublishExecutor } from "../../src/executors/publish-executor.js";

const createdDirectories = new Set<string>();

afterEach(() => {
  for (const directory of createdDirectories) {
    fs.rmSync(directory, { recursive: true, force: true });
  }
  createdDirectories.clear();
});

function createTempWorkspace(): { baseDir: string; databasePath: string } {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "sau-mcp-schedule-runner-"));
  createdDirectories.add(baseDir);
  fs.mkdirSync(path.join(baseDir, "cookies"), { recursive: true });
  fs.writeFileSync(path.join(baseDir, "cookies", "douyin_demo.json"), "{}");
  return {
    baseDir,
    databasePath: path.join(baseDir, "db", "database.db"),
  };
}

describe("schedule runner", () => {
  it("claims one pending schedule and produces one publish task only once", async () => {
    const workspace = createTempWorkspace();
    const app = buildApp(workspace);
    await app.close();

    const database = openDatabase(workspace.databasePath);
    runMigrations(database);
    const scheduleRepository = new ScheduleRepository(database);
    const accountSnapshotRepository = new AccountSnapshotRepository(database);
    const taskRepository = new TaskRepository(database);
    const childTaskRepository = new ChildTaskRepository(database);
    const taskEventRepository = new TaskEventRepository(database);
    const taskService = new TaskService(
      taskRepository,
      childTaskRepository,
      taskEventRepository,
      new AccountExecutor(taskRepository, taskEventRepository, accountSnapshotRepository),
      new PublishExecutor(taskRepository, childTaskRepository, taskEventRepository),
      new TaskControlExecutor(taskRepository, childTaskRepository, taskEventRepository),
    );
    const runner = new ScheduleRunner(scheduleRepository, taskService, "runner-1");

    const created = scheduleRepository.createSchedule({
      source_payload: JSON.stringify({
        trigger_mode: "immediate",
        content_type: "image_text",
        targets: [{ platform: "douyin", account_name: "demo" }],
        materials: [{ type: "image_text", files: ["1.png", "2.png"] }],
        metadata: { title: "图文标题", note: "图文正文", tags: ["旅行"] },
      }),
      trigger_at: "2026-06-08T00:00:00.000Z",
      timezone: "Asia/Shanghai",
    });

    const firstRun = await runner.runDueSchedules("2026-06-08T01:00:00.000Z");
    const secondRun = await runner.runDueSchedules("2026-06-08T01:00:00.000Z");
    const schedule = scheduleRepository.getSchedule(created.schedule_id);

    expect(firstRun.triggeredTaskCount).toBe(1);
    expect(secondRun.triggeredTaskCount).toBe(0);
    expect(schedule?.status).toBe("done");
    expect(schedule?.last_task_id).toMatch(/^task_/);

    database.close();
  });
});
