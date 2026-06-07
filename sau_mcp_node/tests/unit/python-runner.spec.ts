import { describe, expect, it } from "vitest";

import { runPython } from "../../src/bridges/python-runner.js";

describe("python runner", () => {
  it("throws bridge error when python exits non-zero", async () => {
    await expect(
      runPython(["python", "-c", "import sys; sys.stderr.write('boom'); sys.exit(2)"]),
    ).rejects.toMatchObject({
      code: "python_bridge_failed",
    });
  });

  it("returns parsed bridge json even when python exits non-zero", async () => {
    const result = await runPython([
      "python",
      "-c",
      "import json,sys; print(json.dumps({'success': False, 'error': {'code': 'bridge_execution_failed', 'message': 'boom'}}, ensure_ascii=False), end=''); sys.exit(1)",
    ]);

    expect(result).toEqual({
      success: false,
      error: {
        code: "bridge_execution_failed",
        message: "boom",
      },
    });
  });
});
