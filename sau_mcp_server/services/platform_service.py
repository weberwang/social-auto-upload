from __future__ import annotations

from typing import Any

from .models import PlatformCheckRequest, PlatformLoginRequest
from . import platform_adapters


class PlatformService:
    """封装 CLI 与 MCP 共享的平台登录与校验分发能力。"""

    async def login(self, request: PlatformLoginRequest) -> dict[str, Any]:
        """按平台名称把登录请求转发到适配层。"""

        if request.platform == "douyin":
            return await platform_adapters.login_douyin_account(request.account_name, headless=request.headless)
        if request.platform == "kuaishou":
            return await platform_adapters.login_kuaishou_account(request.account_name, headless=request.headless)
        if request.platform == "xiaohongshu":
            return await platform_adapters.login_xiaohongshu_account(request.account_name, headless=request.headless)
        if request.platform == "bilibili":
            return await platform_adapters.login_bilibili_account(request.account_name)
        raise ValueError(f"Unsupported platform: {request.platform}")

    async def check(self, request: PlatformCheckRequest) -> bool:
        """按平台名称把校验请求转发到适配层。"""

        if request.platform == "douyin":
            return await platform_adapters.check_douyin_account(request.account_name)
        if request.platform == "kuaishou":
            return await platform_adapters.check_kuaishou_account(request.account_name)
        if request.platform == "xiaohongshu":
            return await platform_adapters.check_xiaohongshu_account(request.account_name)
        if request.platform == "bilibili":
            return await platform_adapters.check_bilibili_account(request.account_name)
        raise ValueError(f"Unsupported platform: {request.platform}")
