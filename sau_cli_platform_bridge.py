from __future__ import annotations

from sau_mcp_server.services.models import PlatformCheckRequest, PlatformLoginRequest
from sau_mcp_server.services.platform_service import PlatformService

# CLI 和 MCP 共享同一个平台 service 实例，桥接层只负责把参数包装成统一请求。
platform_service = PlatformService()


async def dispatch_platform_login(platform: str, platform_label: str, account_name: str, headless: bool) -> int:
    """把 CLI 登录请求转成共享 service 的统一请求。"""

    result = await platform_service.login(
        PlatformLoginRequest(platform=platform, account_name=account_name, headless=headless)
    )
    if not result["success"]:
        raise RuntimeError(result["message"])
    print(f"{platform_label} login flow completed: {result['account_file']}")
    return 0


async def dispatch_platform_check(platform: str, account_name: str) -> int:
    """把 CLI 校验请求转成共享 service 的统一请求。"""

    is_valid = await platform_service.check(PlatformCheckRequest(platform=platform, account_name=account_name))
    print("valid" if is_valid else "invalid")
    return 0 if is_valid else 1
