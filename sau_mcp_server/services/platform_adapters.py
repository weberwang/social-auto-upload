from __future__ import annotations

from typing import Any

from sau_cli_account_helpers import (
    check_bilibili_account as check_bilibili_account_helper,
    check_douyin_account as check_douyin_account_helper,
    check_kuaishou_account as check_kuaishou_account_helper,
    check_tencent_account as check_tencent_account_helper,
    check_xiaohongshu_account as check_xiaohongshu_account_helper,
    login_bilibili_account as login_bilibili_account_helper,
    login_douyin_account as login_douyin_account_helper,
    login_kuaishou_account as login_kuaishou_account_helper,
    login_tencent_account as login_tencent_account_helper,
    login_xiaohongshu_account as login_xiaohongshu_account_helper,
)


async def login_douyin_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await login_douyin_account_helper(account_name, headless=headless)


async def check_douyin_account(account_name: str) -> bool:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await check_douyin_account_helper(account_name)


async def login_kuaishou_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await login_kuaishou_account_helper(account_name, headless=headless)


async def check_kuaishou_account(account_name: str) -> bool:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await check_kuaishou_account_helper(account_name)


async def login_xiaohongshu_account(account_name: str, headless: bool = True) -> dict[str, Any]:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await login_xiaohongshu_account_helper(account_name, headless=headless)


async def check_xiaohongshu_account(account_name: str) -> bool:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await check_xiaohongshu_account_helper(account_name)


async def login_bilibili_account(account_name: str) -> dict[str, Any]:
    """直接调用账号 helper，保留 Bilibili 的特殊交互签名。"""

    return await login_bilibili_account_helper(account_name)


async def check_bilibili_account(account_name: str) -> bool:
    """直接调用账号 helper，避免适配层回跳 CLI。"""

    return await check_bilibili_account_helper(account_name)
