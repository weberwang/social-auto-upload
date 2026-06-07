import type Database from "better-sqlite3";

type SqliteDatabase = InstanceType<typeof Database>;

import { CURRENT_SCHEMA_VERSION, SCHEMA_V1_SQL } from "./schema.js";

/**
 * 执行 MCP 数据库迁移。
 * Task 2 只有 v1，因此只需在未初始化时把整套表结构落下。
 */
export function runMigrations(database: SqliteDatabase): void {
  database.exec("BEGIN");
  try {
    for (const statement of SCHEMA_V1_SQL) {
      database.exec(statement);
    }
    database
      .prepare(
        `
          INSERT OR IGNORE INTO mcp_schema_migrations (version)
          VALUES (?)
        `,
      )
      .run(CURRENT_SCHEMA_VERSION);
    database.exec("COMMIT");
  } catch (error) {
    database.exec("ROLLBACK");
    throw error;
  }
}
