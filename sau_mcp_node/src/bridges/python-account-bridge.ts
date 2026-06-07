import { runPython, type PythonBridgeSuccess } from "./python-runner.js";

/**
 * 账号登录 bridge 输入。
 * Node 侧先只约束当前 bridge 需要的最小字段。
 */
export type AccountLoginBridgeInput = {
  platform: string;
  account_name: string;
  headless?: boolean;
};

/**
 * 账号校验 bridge 输入。
 */
export type AccountCheckBridgeInput = {
  platform: string;
  account_name: string;
};

function resolvePythonExecutable(): string {
  return process.env.SAU_BRIDGE_PYTHON ?? "python";
}

/**
 * 调 Python 执行账号登录。
 */
export async function runAccountLoginBridge(input: AccountLoginBridgeInput, cwd?: string): Promise<PythonBridgeSuccess> {
  return await runPython(
    [resolvePythonExecutable(), "-m", "sau_bridge", "account-login", "--json-input", JSON.stringify(input)],
    cwd,
  );
}

/**
 * 调 Python 执行账号校验。
 */
export async function runAccountCheckBridge(input: AccountCheckBridgeInput, cwd?: string): Promise<PythonBridgeSuccess> {
  return await runPython(
    [resolvePythonExecutable(), "-m", "sau_bridge", "account-check", "--json-input", JSON.stringify(input)],
    cwd,
  );
}
