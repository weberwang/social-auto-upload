from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Awaitable, Callable

from sau_bridge.account import run_account_check, run_account_login
from sau_bridge.publish import run_publish_note, run_publish_video

BridgeHandler = Callable[[object], Awaitable[dict[str, Any]]]


def _build_parser() -> argparse.ArgumentParser:
    """构建 bridge CLI 解析器。"""

    parser = argparse.ArgumentParser(prog="python -m sau_bridge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("account-login", "account-check", "publish-video", "publish-note"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--json-input", required=True)

    return parser


def _print_json(payload: dict[str, Any]) -> None:
    """统一输出 JSON，确保 stdout 只承载机器可读结果。"""

    print(json.dumps(payload, ensure_ascii=False), end="")


def _parse_json_input(raw_payload: str) -> object:
    """解析 `--json-input`，并把 JSON 错误显式化。"""

    try:
        return json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("json-input must be valid JSON") from exc


async def _run_handler(handler: BridgeHandler, raw_payload: str) -> int:
    """执行 bridge handler，并把异常统一映射为失败 JSON。"""

    try:
        result = await handler(_parse_json_input(raw_payload))
    except Exception as exc:
        _print_json(
            {
                "success": False,
                "error": {
                    "code": "bridge_execution_failed",
                    "message": str(exc),
                },
            }
        )
        return 1

    _print_json(result)
    return 0


def main() -> None:
    """bridge 命令入口。"""

    args = _build_parser().parse_args()
    handler_by_command: dict[str, BridgeHandler] = {
        "account-login": run_account_login,
        "account-check": run_account_check,
        "publish-video": run_publish_video,
        "publish-note": run_publish_note,
    }
    exit_code = asyncio.run(_run_handler(handler_by_command[args.command], args.json_input))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
