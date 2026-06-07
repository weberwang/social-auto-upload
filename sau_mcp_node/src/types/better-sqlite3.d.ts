declare module "better-sqlite3" {
  /**
   * SQLite 执行结果。
   * 这里只声明当前计划阶段会用到的最小字段，避免 Task 2 被第三方类型细节卡住。
   */
  interface RunResult {
    changes: number;
    lastInsertRowid: number | bigint;
  }

  /**
   * SQLite 预编译语句。
   * 先覆盖当前仓储测试实际用到的 `run/get/all` 能力。
   */
  interface Statement<Params extends unknown[] = unknown[], Row = unknown> {
    run(...params: Params): RunResult;
    get(...params: Params): Row | undefined;
    all(...params: Params): Row[];
  }

  /**
   * SQLite 数据库连接。
   * Task 2 只要求最小迁移与查询能力，因此声明保持克制。
   */
  interface DatabaseInstance {
    exec(sql: string): this;
    pragma(sql: string): unknown;
    prepare<Params extends unknown[] = unknown[], Row = unknown>(sql: string): Statement<Params, Row>;
    transaction<TArgs extends unknown[]>(callback: (...args: TArgs) => void): (...args: TArgs) => void;
    close(): void;
  }

  /**
   * better-sqlite3 默认导出构造器。
   * 统一让 Node 侧通过 `new Database(path)` 建立同步连接。
   */
  interface DatabaseConstructor {
    new (filename: string): DatabaseInstance;
  }

  const Database: DatabaseConstructor;

  namespace Database {
    export type Database = DatabaseInstance;
    export type Statement<Params extends unknown[] = unknown[], Row = unknown> = import("better-sqlite3").Statement<
      Params,
      Row
    >;
  }

  export default Database;
}
