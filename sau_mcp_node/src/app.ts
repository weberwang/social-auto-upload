import path from "node:path";

import Fastify, { type FastifyInstance } from "fastify";

import { openDatabase } from "./db/connection.js";
import { runMigrations } from "./db/migrator.js";
import { registerAccountRoutes } from "./http/routes/accounts.js";
import { registerCapabilityRoutes } from "./http/routes/capabilities.js";
import { registerDraftRoutes } from "./http/routes/drafts.js";
import { registerHealthRoutes } from "./http/routes/health.js";
import { registerScheduleRoutes } from "./http/routes/schedules.js";
import { registerTaskEventRoutes } from "./http/routes/task-events.js";
import { registerTaskRoutes } from "./http/routes/tasks.js";
import { registerToolRoutes } from "./http/routes/tools.js";
import { AccountExecutor } from "./executors/account-executor.js";
import { PublishExecutor } from "./executors/publish-executor.js";
import { TaskControlExecutor } from "./executors/task-control-executor.js";
import { AccountSnapshotRepository } from "./repositories/account-snapshot-repository.js";
import { ChildTaskRepository } from "./repositories/child-task-repository.js";
import { DraftRepository } from "./repositories/draft-repository.js";
import { ScheduleRepository } from "./repositories/schedule-repository.js";
import { TaskEventRepository } from "./repositories/task-event-repository.js";
import { TaskRepository } from "./repositories/task-repository.js";
import { resolveBaseDir } from "./shared/base-dir.js";
import { AccountService } from "./services/account-service.js";
import { DraftService } from "./services/draft-service.js";
import { ScheduleService } from "./services/schedule-service.js";
import { TaskService } from "./services/task-service.js";

export type BuildAppOptions = {
  baseDir?: string;
  databasePath?: string;
};

/**
 * 构建 Node MCP Fastify 应用。
 * 这里统一串起数据库迁移与旧草稿导入，避免调用方忘记执行兼容初始化。
 */
export function buildApp(options: BuildAppOptions = {}): FastifyInstance {
  const baseDir = resolveBaseDir(options.baseDir);
  const databasePath = options.databasePath ?? path.join(baseDir, "db", "database.db");
  const database = openDatabase(databasePath);

  runMigrations(database);
  new DraftRepository(database).importLegacyDrafts();

  const app = Fastify();
  const accountService = new AccountService(database, baseDir);
  const draftService = new DraftService(database);
  const scheduleService = new ScheduleService(database);
  const scheduleRepository = new ScheduleRepository(database);
  const taskRepository = new TaskRepository(database);
  const childTaskRepository = new ChildTaskRepository(database);
  const taskEventRepository = new TaskEventRepository(database);
  const accountSnapshotRepository = new AccountSnapshotRepository(database);
  const taskService = new TaskService(
    taskRepository,
    childTaskRepository,
    taskEventRepository,
    new AccountExecutor(taskRepository, taskEventRepository, accountSnapshotRepository),
    new PublishExecutor(taskRepository, childTaskRepository, taskEventRepository),
    new TaskControlExecutor(taskRepository, childTaskRepository, taskEventRepository),
  );

  registerHealthRoutes(app);
  registerCapabilityRoutes(app);
  registerAccountRoutes(app, accountService);
  registerDraftRoutes(app, draftService);
  registerScheduleRoutes(app, scheduleService);
  registerTaskRoutes(app, taskService);
  registerTaskEventRoutes(app, taskService);
  registerToolRoutes(app, taskService, draftService, scheduleService);

  app.addHook("onClose", async () => {
    database.close();
  });

  return app;
}
