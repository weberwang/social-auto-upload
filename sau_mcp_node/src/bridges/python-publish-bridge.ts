import { runPython, type PythonBridgeSuccess } from "./python-runner.js";

export type PublishVideoBridgeInput = {
  platform: string;
  account_name: string;
  file_path: string;
  title: string;
  description?: string;
  tags?: string[];
  schedule?: string | null;
  tid?: number | null;
};

export type PublishNoteBridgeInput = {
  platform: string;
  account_name: string;
  image_files: string[];
  title: string;
  note: string;
  tags?: string[];
  schedule?: string | null;
};

function resolvePythonExecutable(): string {
  return process.env.SAU_BRIDGE_PYTHON ?? "python";
}

/**
 * 调 Python 执行视频发布。
 */
export async function runPublishVideoBridge(input: PublishVideoBridgeInput, cwd?: string): Promise<PythonBridgeSuccess> {
  return await runPython(
    [resolvePythonExecutable(), "-m", "sau_bridge", "publish-video", "--json-input", JSON.stringify(input)],
    cwd,
  );
}

/**
 * 调 Python 执行图文发布。
 */
export async function runPublishNoteBridge(input: PublishNoteBridgeInput, cwd?: string): Promise<PythonBridgeSuccess> {
  return await runPython(
    [resolvePythonExecutable(), "-m", "sau_bridge", "publish-note", "--json-input", JSON.stringify(input)],
    cwd,
  );
}
