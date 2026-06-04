from __future__ import annotations

import re
from pathlib import Path

from conf import BASE_DIR
from uploader.bilibili_uploader.runtime import run_biliup_command
from uploader.douyin_uploader.main import cookie_auth as douyin_cookie_auth, douyin_setup
from uploader.ks_uploader.main import cookie_auth as kuaishou_cookie_auth, ks_setup
from uploader.tencent_uploader.main import cookie_auth as tencent_cookie_auth, tencent_setup
from uploader.xiaohongshu_uploader.main import (
    cookie_auth as xiaohongshu_cookie_auth,
    xiaohongshu_setup,
)

_ACCOUNT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def has_interactive_terminal() -> bool:
    """判断当前环境是否适合 Bilibili 这类需要本地交互的登录流程。"""

    import sys

    return sys.stdin.isatty() and sys.stdout.isatty()


def resolve_runtime_home() -> Path:
    """统一返回 CLI 使用的运行根目录。"""

    return Path(BASE_DIR)


def _require_safe_account_name(account_name: str) -> str:
    """只允许字母、数字、下划线和连字符，避免账号名携带路径语义。"""

    if not isinstance(account_name, str) or not account_name.strip():
        raise ValueError("account_name must be a non-empty string")
    if not _ACCOUNT_NAME_PATTERN.fullmatch(account_name):
        raise ValueError("account_name may only contain letters, numbers, underscores, and hyphens")
    return account_name


def resolve_account_file(platform: str, account_name: str) -> Path:
    """按平台和账号生成本地 cookie 文件路径，并阻止越界到 cookies 目录外。"""

    safe_account_name = _require_safe_account_name(account_name)
    cookies_dir = resolve_runtime_home() / "cookies"
    account_file = cookies_dir / f"{platform}_{safe_account_name}.json"

    # 先做一次归一化检查，确保任何平台或账号拼接后的结果都留在 cookies 根目录内。
    resolved_cookies_dir = cookies_dir.resolve()
    resolved_account_file = account_file.resolve()
    try:
        resolved_account_file.relative_to(resolved_cookies_dir)
    except ValueError as exc:
        raise ValueError("account_file must stay inside cookies directory") from exc

    cookies_dir.mkdir(parents=True, exist_ok=True)
    return account_file


async def login_douyin_account(account_name: str, headless: bool = True) -> dict:
    """调用 Douyin 登录适配器。"""

    account_file = resolve_account_file("douyin", account_name)
    return await douyin_setup(str(account_file), handle=True, return_detail=True, headless=headless)


async def check_douyin_account(account_name: str) -> bool:
    """调用 Douyin 账号校验适配器。"""

    account_file = resolve_account_file("douyin", account_name)
    if not account_file.exists():
        return False
    return await douyin_cookie_auth(str(account_file))


async def login_kuaishou_account(account_name: str, headless: bool = True) -> dict:
    """调用 Kuaishou 登录适配器。"""

    account_file = resolve_account_file("kuaishou", account_name)
    return await ks_setup(str(account_file), handle=True, return_detail=True, headless=headless)


async def check_kuaishou_account(account_name: str) -> bool:
    """调用 Kuaishou 账号校验适配器。"""

    account_file = resolve_account_file("kuaishou", account_name)
    if not account_file.exists():
        return False
    return await kuaishou_cookie_auth(str(account_file))


async def login_xiaohongshu_account(account_name: str, headless: bool = True) -> dict:
    """调用小红书登录适配器。"""

    account_file = resolve_account_file("xiaohongshu", account_name)
    return await xiaohongshu_setup(str(account_file), handle=True, return_detail=True, headless=headless)


async def check_xiaohongshu_account(account_name: str) -> bool:
    """调用小红书账号校验适配器。"""

    account_file = resolve_account_file("xiaohongshu", account_name)
    if not account_file.exists():
        return False
    return await xiaohongshu_cookie_auth(str(account_file))


async def login_bilibili_account(account_name: str) -> dict:
    """调用 Bilibili 登录适配器，并保留本地交互提示。"""

    account_file = resolve_account_file("bilibili", account_name)
    if not has_interactive_terminal():
        return {
            "success": False,
            "message": (
                "Bilibili login requires a local interactive terminal. "
                f"Please run `sau bilibili login --account {account_name}` yourself in a local terminal. "
                "If the terminal QR code does not render completely, open `./qrcode.png` and scan that image."
            ),
            "account_file": str(account_file),
        }

    result = run_biliup_command(["-u", str(account_file), "login"], interactive=True)
    success = result.returncode == 0
    return {
        "success": success,
        "message": (result.stderr or result.stdout or "").strip() or "Bilibili login completed" if success else (result.stderr or result.stdout or "").strip() or "Bilibili login failed",
        "account_file": str(account_file),
    }


async def check_bilibili_account(account_name: str) -> bool:
    """调用 Bilibili 账号校验适配器。"""

    account_file = resolve_account_file("bilibili", account_name)
    if not account_file.exists():
        return False
    result = run_biliup_command(["-u", str(account_file), "renew"])
    return result.returncode == 0


async def login_tencent_account(account_name: str, headless: bool = True) -> dict:
    """调用 Tencent/WeChat Channels 登录适配器。"""

    account_file = resolve_account_file("tencent", account_name)
    return await tencent_setup(str(account_file), handle=True, return_detail=True, headless=headless)


async def check_tencent_account(account_name: str) -> bool:
    """调用 Tencent/WeChat Channels 账号校验适配器。"""

    account_file = resolve_account_file("tencent", account_name)
    if not account_file.exists():
        return False
    return await tencent_cookie_auth(str(account_file))
