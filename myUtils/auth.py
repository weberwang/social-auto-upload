import asyncio
import configparser
import os
from pathlib import Path
from typing import Awaitable, Callable

from playwright.async_api import Error as PlaywrightError, async_playwright
from xhs import XhsClient

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from myUtils.bilibili_web_bridge import check_bilibili_account_file
from uploader.douyin_uploader.main import cookie_auth as mainline_douyin_cookie_auth
from uploader.tencent_uploader.main import cookie_auth as mainline_tencent_cookie_auth
from uploader.wechatmp_uploader.main import cookie_auth as mainline_wechatmp_cookie_auth
from uploader.xhs_uploader.main import sign_local
from utils.base_social_media import set_init_script
from utils.log import wechatmp_logger, tencent_logger, kuaishou_logger, douyin_logger, xhs_logger


def _is_missing_playwright_browser_error(error: PlaywrightError) -> bool:
    """判断是否因为本机未安装 Playwright 浏览器而导致启动失败。"""
    message = str(error)
    return "Executable doesn't exist" in message and (
        "ms-playwright" in message
        or "headless_shell" in message
        or "chrome-win" in message
    )


async def _run_cookie_validator(
    validator: Callable[[Path], Awaitable[bool]],
    account_file: Path,
    logger,
    platform_name: str,
) -> bool:
    """执行单个平台 Cookie 校验，并把浏览器缺失降级成可控失败。"""
    try:
        return await validator(account_file)
    except PlaywrightError as error:
        if _is_missing_playwright_browser_error(error):
            # 这里返回 False 而不是继续抛异常，避免账号列表接口因为本机环境未初始化直接 500。
            logger.error(
                f"[+] {platform_name} Cookie 校验失败：未找到 Playwright 浏览器，请先执行 `playwright install chromium`"
            )
            return False
        raise


async def cookie_auth_douyin(account_file):
    """复用主线抖音 Cookie 校验器，避免登录与账号列表走两套不同的页面探测逻辑。"""

    return await mainline_douyin_cookie_auth(account_file)


async def cookie_auth_tencent(account_file):
    """复用主线视频号 Cookie 校验器，确保登录与账号列表共享同一套浏览器策略。"""

    return await mainline_tencent_cookie_auth(account_file)


async def cookie_auth_wechatmp(account_file):
    """复用主线微信公众号 Cookie 校验器，避免历史 Web 与主线判断分叉。"""

    return await mainline_wechatmp_cookie_auth(account_file)


async def cookie_auth_ks(account_file):
    """校验快手账号 Cookie 是否仍然有效。"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒

            kuaishou_logger.info("[+] 等待5秒 cookie 失效")
            return False
        except:
            kuaishou_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_xhs(account_file):
    """校验小红书账号 Cookie 是否仍然有效。"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def check_cookie(type, file_path):
    """按平台类型分发 Cookie 校验逻辑。"""
    account_file = Path(BASE_DIR / "cookiesFile" / file_path)
    match type:
        # 小红书
        case 1:
            return await _run_cookie_validator(cookie_auth_xhs, account_file, xhs_logger, "小红书")
        # 视频号
        case 2:
            return await _run_cookie_validator(cookie_auth_tencent, account_file, tencent_logger, "视频号")
        # 抖音
        case 3:
            return await _run_cookie_validator(cookie_auth_douyin, account_file, douyin_logger, "抖音")
        # 快手
        case 4:
            return await _run_cookie_validator(cookie_auth_ks, account_file, kuaishou_logger, "快手")
        # B站
        case 5:
            # B站校验不依赖 Playwright，而是直接走 biliup renew，因此单独用同步桥接函数。
            return check_bilibili_account_file(file_path)
        # 微信公众号
        case 6:
            return await _run_cookie_validator(cookie_auth_wechatmp, account_file, wechatmp_logger, "微信公众号")
        case _:
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)
