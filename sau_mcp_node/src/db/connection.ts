import fs from "node:fs";
import path from "node:path";

import Database from "better-sqlite3";

type SqliteDatabase = InstanceType<typeof Database>;

/**
 * 打开 SQLite 连接。
 * 统一在这里补目录创建与常用 pragma，避免各仓储自己拼连接细节。
 */
export function openDatabase(databasePath: string): SqliteDatabase {
  fs.mkdirSync(path.dirname(databasePath), { recursive: true });
  const database = new Database(databasePath);
  database.pragma("journal_mode = WAL");
  database.pragma("foreign_keys = ON");
  database.pragma("busy_timeout = 5000");
  return database;
}
