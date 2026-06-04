from __future__ import annotations

from sau_mcp_server.services.account_service import AccountService


class CapabilityService:
    """集中维护 MCP 对外暴露的工具、平台与账号能力矩阵。"""

    def __init__(self, account_service: AccountService) -> None:
        """保存账号服务引用，便于能力接口顺带暴露本地可用账号。"""

        self.account_service = account_service
        self._tools = [
            "platform_login",
            "platform_check",
        ]
        self._platforms = ["douyin", "kuaishou", "xiaohongshu", "bilibili"]

    def get_capabilities(self) -> dict[str, object]:
        """返回 MCP 客户端可直接消费的能力矩阵。"""

        return {
            "tools": list(self._tools),
            "platforms": list(self._platforms),
            # 账号列表先基于本地文件系统枚举，后续如果有数据库或仓储再替换实现。
            "accounts": self.account_service.list_accounts_by_platform(self._platforms),
        }
