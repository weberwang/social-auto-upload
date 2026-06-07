import { spawn } from "node:child_process";

/**
 * Python bridge 成功返回结构。
 * Node 侧后续所有账号/发布桥接都统一消费这个协议。
 */
export type PythonBridgeSuccess = {
  success: boolean;
  data?: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
  };
};

/**
 * 执行 Python 子进程并解析标准 JSON 输出。
 * stderr 只用于错误上下文，stdout 必须是完整 JSON。
 */
export async function runPython(command: string[], cwd?: string): Promise<PythonBridgeSuccess> {
  return await new Promise<PythonBridgeSuccess>((resolve, reject) => {
    const child = spawn(command[0]!, command.slice(1), {
      cwd,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk: Buffer | string) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk: Buffer | string) => {
      stderr += chunk.toString();
    });
    child.on("error", (error) => {
      reject({
        code: "python_bridge_failed",
        message: `${String(error)}${stderr ? `: ${stderr.trim()}` : ""}`,
      });
    });
    child.on("close", (code) => {
      if (stdout.trim()) {
        try {
          const parsed = JSON.parse(stdout) as PythonBridgeSuccess;
          resolve(parsed);
          return;
        } catch {
          // 只有在 stdout 不是有效 JSON 时，才继续按退出码走错误映射。
        }
      }

      if (code !== 0) {
        reject({
          code: "python_bridge_failed",
          message: stderr.trim() || stdout.trim() || `python exited with code ${code ?? "unknown"}`,
        });
        return;
      }
      reject({
        code: "python_bridge_invalid_json",
        message: "python bridge exited successfully but returned empty or invalid JSON",
      });
    });
  });
}
