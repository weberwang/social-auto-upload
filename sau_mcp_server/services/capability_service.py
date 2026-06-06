from __future__ import annotations

from typing import Final

from sau_mcp_server.services.account_service import AccountService

PLATFORM_DETAIL_BY_NAME: Final[dict[str, dict[str, str | list[str]]]] = {
    "douyin": {
        "display_name": "抖音",
        # 抖音当前主线同时具备视频与图文能力，这里显式暴露给客户端做细粒度展示。
        "supported_material_types": ["video", "image_text"],
    },
    "kuaishou": {
        "display_name": "快手",
        "supported_material_types": ["video", "image_text"],
    },
    "xiaohongshu": {
        "display_name": "小红书",
        "supported_material_types": ["video", "image_text"],
    },
    "bilibili": {
        "display_name": "B站",
        "supported_material_types": ["video"],
    },
}


class CapabilityService:
    """集中维护 MCP 对外暴露的工具、平台与账号能力矩阵。"""

    def __init__(self, account_service: AccountService) -> None:
        """保存账号服务引用，便于能力接口顺带暴露本地可用账号。"""

        self.account_service = account_service
        self._tools = [
            "platform_login",
            "platform_check",
        ]
        self._platforms = list(PLATFORM_DETAIL_BY_NAME.keys())

    def get_capabilities(self) -> dict[str, object]:
        """返回 MCP 客户端可直接消费的能力矩阵。"""

        return {
            "tools": list(self._tools),
            "platforms": list(self._platforms),
            # 平台明细与 platforms 列表并存，兼顾老客户端兼容和新客户端精细展示。
            "platform_details": dict(PLATFORM_DETAIL_BY_NAME),
            # 账号列表先基于本地文件系统枚举，后续如果有数据库或仓储再替换实现。
            "accounts": self.account_service.list_accounts_by_platform(self._platforms),
        }
