import { buildApp } from "./app.js";

type CliOptions = {
  host: string;
  port: number;
};

function parseCliOptions(argv: string[]): CliOptions {
  let host = process.env.SAU_MCP_HOST ?? "127.0.0.1";
  let port = Number.parseInt(process.env.SAU_MCP_PORT ?? "5410", 10);

  for (let index = 0; index < argv.length; index += 1) {
    const current = argv[index];
    const next = argv[index + 1];
    if (current === "--host" && next) {
      host = next;
      index += 1;
      continue;
    }
    if (current === "--port" && next) {
      port = Number.parseInt(next, 10);
      index += 1;
    }
  }

  if (!Number.isInteger(port) || port <= 0) {
    throw new Error("port must be a positive integer");
  }

  return { host, port };
}

/**
 * Node MCP CLI 入口。
 * 统一从参数和环境变量读取 host/port，并直接启动 Fastify 服务。
 */
export async function main(argv: string[] = process.argv.slice(2)): Promise<void> {
  const options = parseCliOptions(argv);
  const app = buildApp();
  await app.listen({
    host: options.host,
    port: options.port,
  });
}

if (import.meta.url === `file://${process.argv[1]?.replaceAll("\\", "/")}`) {
  void main().catch((error: unknown) => {
    // 启动失败时直接打印到 stderr，方便 sau_mcp_launcher 感知失败。
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
