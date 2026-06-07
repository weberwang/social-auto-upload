from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from conf import BASE_DIR


@dataclass(frozen=True, slots=True)
class AccountLoginPayload:
    """描述一次账号登录 bridge 请求。"""

    platform: str
    account_name: str
    headless: bool = True


@dataclass(frozen=True, slots=True)
class AccountCheckPayload:
    """描述一次账号校验 bridge 请求。"""

    platform: str
    account_name: str


_ACCOUNT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _require_non_empty_string(field_name: str, value: object) -> str:
    """把 bridge 输入约束为非空文本，避免隐式字符串化脏值。"""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_safe_account_name(account_name: str) -> str:
    """复用主线账号命名约束，避免 bridge 放宽本地文件边界。"""

    normalized = _require_non_empty_string("account_name", account_name)
    if not _ACCOUNT_NAME_PATTERN.fullmatch(normalized):
        raise ValueError("account_name may only contain letters, numbers, underscores, and hyphens")
    return normalized


def _resolve_account_file(platform: str, account_name: str) -> Path:
    """在 bridge 层直接解析账号文件路径，避免只做存在性判断时提前导入全量 helper。"""

    return Path(BASE_DIR) / "cookies" / f"{platform}_{_require_safe_account_name(account_name)}.json"


def _parse_login_payload(payload: object) -> AccountLoginPayload:
    """把原始 JSON payload 解析为登录请求对象。"""

    if not isinstance(payload, dict):
        raise ValueError("account-login payload must be an object")
    platform = _require_non_empty_string("platform", payload.get("platform"))
    account_name = _require_non_empty_string("account_name", payload.get("account_name"))
    headless = payload.get("headless", True)
    if not isinstance(headless, bool):
        raise ValueError("headless must be a boolean")
    return AccountLoginPayload(platform=platform, account_name=account_name, headless=headless)


def _parse_check_payload(payload: object) -> AccountCheckPayload:
    """把原始 JSON payload 解析为账号校验请求对象。"""

    if not isinstance(payload, dict):
        raise ValueError("account-check payload must be an object")
    platform = _require_non_empty_string("platform", payload.get("platform"))
    account_name = _require_non_empty_string("account_name", payload.get("account_name"))
    return AccountCheckPayload(platform=platform, account_name=account_name)


async def run_account_login(payload: object) -> dict[str, Any]:
    """执行账号登录并返回统一 bridge JSON。"""

    request = _parse_login_payload(payload)
    if request.platform == "douyin":
        from sau_cli_account_helpers import login_douyin_account

        result = await login_douyin_account(request.account_name, headless=request.headless)
    elif request.platform == "kuaishou":
        from sau_cli_account_helpers import login_kuaishou_account

        result = await login_kuaishou_account(request.account_name, headless=request.headless)
    elif request.platform == "xiaohongshu":
        from sau_cli_account_helpers import login_xiaohongshu_account

        result = await login_xiaohongshu_account(request.account_name, headless=request.headless)
    elif request.platform == "bilibili":
        from sau_cli_account_helpers import login_bilibili_account

        result = await login_bilibili_account(request.account_name)
    elif request.platform == "tencent":
        from sau_cli_account_helpers import login_tencent_account

        result = await login_tencent_account(request.account_name, headless=request.headless)
    else:
        raise ValueError(f"unsupported platform: {request.platform}")

    return {"success": bool(result.get("success", False)), "data": result}


async def run_account_check(payload: object) -> dict[str, Any]:
    """执行账号校验并返回统一 bridge JSON。"""

    request = _parse_check_payload(payload)
    if not _resolve_account_file(request.platform, request.account_name).exists():
        return {"success": True, "data": {"valid": False}}

    if request.platform == "douyin":
        from sau_cli_account_helpers import check_douyin_account

        valid = await check_douyin_account(request.account_name)
    elif request.platform == "kuaishou":
        from sau_cli_account_helpers import check_kuaishou_account

        valid = await check_kuaishou_account(request.account_name)
    elif request.platform == "xiaohongshu":
        from sau_cli_account_helpers import check_xiaohongshu_account

        valid = await check_xiaohongshu_account(request.account_name)
    elif request.platform == "bilibili":
        from sau_cli_account_helpers import check_bilibili_account

        valid = await check_bilibili_account(request.account_name)
    elif request.platform == "tencent":
        from sau_cli_account_helpers import check_tencent_account

        valid = await check_tencent_account(request.account_name)
    else:
        raise ValueError(f"unsupported platform: {request.platform}")

    return {"success": True, "data": {"valid": valid}}
