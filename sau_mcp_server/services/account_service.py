from __future__ import annotations

from pathlib import Path

from conf import BASE_DIR


class AccountService:
    """基于本地 cookie 文件名约定，枚举各平台可用账号。"""

    def __init__(self, runtime_home: Path | None = None) -> None:
        """保存运行根目录，便于测试时注入临时目录。"""

        self.runtime_home = Path(runtime_home) if runtime_home is not None else Path(BASE_DIR)

    def list_accounts(self, platform: str) -> list[str]:
        """按平台扫描 `cookies` 目录，提取 `account_name` 列表。"""

        cookies_dir = self.runtime_home / "cookies"
        if not cookies_dir.exists():
            return []

        prefix = f"{platform}_"
        accounts: list[str] = []
        # 当前账号文件采用 `platform_account.json` 命名，这里只做最小枚举，不引入数据库依赖。
        for account_file in sorted(cookies_dir.glob(f"{platform}_*.json")):
            account_name = account_file.stem[len(prefix) :]
            if account_name:
                accounts.append(account_name)
        return accounts

    def list_accounts_by_platform(self, platforms: list[str]) -> dict[str, list[str]]:
        """批量返回平台到账号列表的映射，供能力矩阵直接消费。"""

        return {platform: self.list_accounts(platform) for platform in platforms}
