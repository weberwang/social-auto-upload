import path from "node:path";

/**
 * 解析 MCP 服务运行根目录。
 * 默认以仓库根目录为基准，后续也允许测试显式覆盖。
 */
export function resolveBaseDir(explicitBaseDir?: string): string {
  return explicitBaseDir ?? path.resolve(process.cwd(), "..");
}
