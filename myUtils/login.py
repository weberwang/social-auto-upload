import asyncio
import base64
import io
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import segno
from playwright.async_api import async_playwright

from myUtils.auth import check_cookie
from myUtils.bilibili_web_bridge import build_biliup_account_payload
from uploader.douyin_uploader.main import douyin_cookie_gen as mainline_douyin_cookie_gen
from uploader.tencent_uploader.main import get_tencent_cookie as mainline_tencent_cookie_gen
from uploader.wechatmp_uploader.main import get_wechatmp_cookie as mainline_wechatmp_cookie_gen
from utils.base_social_media import set_init_script
from utils.log import bilibili_logger
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH

# 统一获取浏览器启动配置（防风控+引入本地浏览器）
def get_browser_options():
    options = {
        'headless': LOCAL_CHROME_HEADLESS,
        'args': [
            '--disable-blink-features=AutomationControlled',  # 核心防爬屏蔽：去掉 window.navigator.webdriver 标签
            '--lang=zh-CN',
            '--disable-infobars',
            '--start-maximized'
        ]
    }
    # 如果用户在 conf.py 里配置了本地 Chrome，就用本地的，这样成功率极高
    if LOCAL_CHROME_PATH:
        options['executable_path'] = LOCAL_CHROME_PATH

    return options

async def _push_douyin_qrcode_to_status_queue(qrcode_info, status_queue):
    """把主线登录流程产出的二维码透传给历史 Web SSE 队列。"""
    image_data_url = qrcode_info.get("image_data_url") if qrcode_info else ""
    if image_data_url:
        print("✅ 图片地址:", image_data_url)
        status_queue.put(image_data_url)


async def _push_tencent_qrcode_to_status_queue(qrcode_info, status_queue):
    """把主线视频号登录流程产出的二维码透传给历史 Web SSE 队列。"""

    image_data_url = qrcode_info.get("image_data_url") if qrcode_info else ""
    if image_data_url:
        print("视频号二维码地址:", image_data_url)
        status_queue.put(image_data_url)


async def _push_wechatmp_qrcode_to_status_queue(qrcode_info, status_queue):
    """把主线微信公众号登录流程产出的二维码透传给历史 Web SSE 队列。"""

    image_data_url = qrcode_info.get("image_data_url") if qrcode_info else ""
    if image_data_url:
        image_path = str(qrcode_info.get("image_path") or "")
        payload_length = int(qrcode_info.get("payload_length") or len(image_data_url))
        image_byte_size = int(qrcode_info.get("image_byte_size") or 0)
        debug_message = (
            "LOG:微信公众号:qr_ready:"
            f"path={image_path};payload_length={payload_length};image_bytes={image_byte_size}"
        )
        # 先把二维码载荷元数据透传给前端控制台，方便判断是“没生成”还是“生成了但没展示”。
        print(f"微信公众号二维码调试事件: {debug_message}")
        status_queue.put(debug_message)
        print("微信公众号二维码地址:", image_data_url)
        status_queue.put(image_data_url)


def _push_wechatmp_debug_to_status_queue(status_queue, stage: str, detail: str) -> None:
    """把公众号登录桥接层的关键阶段透传到历史 Web SSE，方便前端控制台对照时序。"""

    debug_message = f"LOG:微信公众号:{stage}:{detail}"
    print(f"微信公众号调试事件: {debug_message}")
    status_queue.put(debug_message)


async def _push_tencent_debug_to_status_queue(status_event, status_queue):
    """把主线视频号登录调试事件透传给历史 Web SSE，便于前后端同时定位卡点。"""

    if not isinstance(status_event, dict):
        return

    stage = str(status_event.get("stage") or "unknown")
    detail = str(status_event.get("detail") or "")
    debug_message = f"LOG:视频号:{stage}:{detail}"
    print(f"视频号调试事件: {debug_message}")
    status_queue.put(debug_message)


def _build_qrcode_data_url(qrcode_content: str) -> str:
    """把二维码内容转成 PNG data URL，便于历史 Web 直接通过 SSE 展示。"""

    image_buffer = io.BytesIO()
    segno.make(qrcode_content).save(image_buffer, kind="png", scale=8, border=2)
    base64_image = base64.b64encode(image_buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{base64_image}"


def _save_user_info_record(platform_type: int, account_file_name: str, user_name: str) -> None:
    """统一写入历史 Web 的账号表，避免各平台重复散落同一段 SQL。"""

    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO user_info (type, filePath, userName, status)
            VALUES (?, ?, ?, ?)
            ''',
            (platform_type, account_file_name, user_name, 1),
        )
        conn.commit()
        print("✅ 用户状态已记录")


def _push_login_error(status_queue, user_message: str) -> None:
    """统一把登录失败信息推给前端 SSE，并保留终态码兼容现有页面流程。"""

    if user_message:
        status_queue.put(f"ERROR:{user_message}")
    status_queue.put("500")


def _apply_bilibili_login_result(bili_client: Any, login_result: dict) -> None:
    """把 biliup 二维码登录响应写回客户端对象，随后复用其 `store()` 持久化账号文件。"""

    if (
        not login_result
        or login_result.get("code") != 0
        or login_result.get("data") is None
        or login_result["data"].get("cookie_info") is None
    ):
        raise RuntimeError(login_result or "B站二维码登录失败")

    session = getattr(bili_client, "_BiliBili__session")
    cookie_info = login_result["data"]["cookie_info"]["cookies"]
    for cookie in cookie_info:
        session.cookies.set(cookie["name"], cookie["value"])

    bili_client.cookies = session.cookies.get_dict()
    token_info = login_result["data"].get("token_info", {})
    bili_client.access_token = token_info.get("access_token")
    bili_client.refresh_token = token_info.get("refresh_token")


def _store_bilibili_account_file(account_file: Path, bili_client: Any) -> None:
    """把 B 站登录态持久化成 biliup CLI 可直接读取的账号文件结构。"""

    raw_payload = {
        **(bili_client.cookies or {}),
        "access_token": bili_client.access_token or "",
        "refresh_token": bili_client.refresh_token or "",
    }
    normalized_payload = build_biliup_account_payload(raw_payload)
    account_file.write_text(
        json.dumps(normalized_payload, ensure_ascii=False),
        encoding="utf-8",
    )


async def bilibili_cookie_gen(id, status_queue):
    """历史 Web B站登录入口，直接复用 biliup 提供的二维码登录 API。"""

    uuid_v1 = uuid.uuid1()
    print(f"UUID v1: {uuid_v1}")

    cookies_dir = Path(BASE_DIR / "cookiesFile")
    cookies_dir.mkdir(exist_ok=True)
    account_file = cookies_dir / f"{uuid_v1}.json"

    try:
        from biliup.plugins.bili_webup import BiliBili, Data

        bili_client = BiliBili(Data())
        qrcode_result = bili_client.get_qrcode()
        qrcode_url = qrcode_result.get("data", {}).get("url") if qrcode_result else ""
        if not qrcode_url:
            raise RuntimeError(qrcode_result or "B站二维码获取失败")

        image_data_url = _build_qrcode_data_url(qrcode_url)
        print("✅ 图片地址:", image_data_url[:80] + "...")
        status_queue.put(image_data_url)
        bilibili_logger.info("B站二维码已生成，等待用户扫码确认")

        login_result = await bili_client.login_by_qrcode(qrcode_result)
        _apply_bilibili_login_result(bili_client, login_result)
        _store_bilibili_account_file(account_file, bili_client)
    except Exception as exc:
        bilibili_logger.exception(f"B站登录失败，账号名={id}，错误={exc}")
        print(f"B站登录失败: {exc}")
        _push_login_error(status_queue, f"B站登录失败：{exc}")
        return None

    result = await check_cookie(5, account_file.name)
    if not result:
        bilibili_logger.error(f"B站登录完成但账号校验失败，账号名={id}，文件={account_file.name}")
        _push_login_error(status_queue, "B站登录完成，但账号校验失败")
        return None

    _save_user_info_record(5, account_file.name, id)
    bilibili_logger.success(f"B站登录成功，账号名={id}，文件={account_file.name}")
    status_queue.put("200")
    return account_file


# 抖音登录
async def douyin_cookie_gen(id, status_queue):
    """历史 Web 抖音登录入口，复用主线扫码轮询逻辑，避免再依赖 URL 跳转判断成功。"""
    uuid_v1 = uuid.uuid1()
    print(f"UUID v1: {uuid_v1}")

    # 旧 Web 仍然使用 cookiesFile 目录存储账号文件，这里保持原有数据布局不变。
    cookies_dir = Path(BASE_DIR / "cookiesFile")
    cookies_dir.mkdir(exist_ok=True)
    account_file = cookies_dir / f"{uuid_v1}.json"

    result = await mainline_douyin_cookie_gen(
        str(account_file),
        qrcode_callback=lambda qrcode_info: _push_douyin_qrcode_to_status_queue(
            qrcode_info, status_queue
        ),
        headless=LOCAL_CHROME_HEADLESS,
    )

    if not result.get("success"):
        status_queue.put("500")
        return None

    _save_user_info_record(3, account_file.name, id)

    status_queue.put("200")


# 视频号登录
async def get_tencent_cookie(id, status_queue, cancel_event=None, session_id: str = ""):
    """历史 Web 视频号登录入口，复用主线扫码轮询逻辑，避免继续依赖 URL 跳转判定。"""

    uuid_v1 = uuid.uuid1()
    print(f"UUID v1: {uuid_v1}")

    # 历史 Web 仍然使用 cookiesFile 目录存储账号文件，这里显式传绝对路径给主线登录器。
    cookies_dir = Path(BASE_DIR / "cookiesFile")
    cookies_dir.mkdir(exist_ok=True)
    account_file = cookies_dir / f"{uuid_v1}.json"
    await _push_tencent_debug_to_status_queue(
        {"stage": "legacy_login_start", "detail": f"历史Web视频号登录开始，账号={id}"},
        status_queue,
    )
    await _push_tencent_debug_to_status_queue(
        {"stage": "legacy_browser_mode", "detail": "历史Web视频号登录强制使用有头浏览器，规避无头风控"},
        status_queue,
    )

    result = await mainline_tencent_cookie_gen(
        str(account_file),
        qrcode_callback=lambda qrcode_info: _push_tencent_qrcode_to_status_queue(
            qrcode_info, status_queue
        ),
        status_callback=lambda status_event: _push_tencent_debug_to_status_queue(
            status_event, status_queue
        ),
        cancel_event=cancel_event,
        # 视频号扫码登录强依赖接近真实浏览器环境；实测无头模式更容易被平台停留在 login.html。
        headless=False,
    )

    if result.get("status") == "cancelled":
        await _push_tencent_debug_to_status_queue(
            {
                "stage": "legacy_login_cancelled",
                "detail": f"历史Web视频号登录已取消，session_id={session_id or 'unknown'}",
            },
            status_queue,
        )
        return None

    if not result.get("success"):
        # 主线登录器已经覆盖了“已扫码待确认 / 页面未跳转 / cookie 校验失败”等新页面分支。
        await _push_tencent_debug_to_status_queue(
            {
                "stage": "legacy_login_failed",
                "detail": result.get("message", "视频号登录失败"),
            },
            status_queue,
        )
        _push_login_error(status_queue, result.get("message", "视频号登录失败"))
        return None

    await _push_tencent_debug_to_status_queue(
        {
            "stage": "legacy_login_success",
            "detail": f"账号文件已落盘: {account_file.name}",
        },
        status_queue,
    )
    _save_user_info_record(2, account_file.name, id)
    status_queue.put("200")
    return account_file


async def get_wechatmp_cookie(id, status_queue):
    """历史 Web 微信公众号登录入口，复用主线扫码流程并沿用既有账号落库方式。"""

    uuid_v1 = uuid.uuid1()
    print(f"UUID v1: {uuid_v1}")

    cookies_dir = Path(BASE_DIR / "cookiesFile")
    cookies_dir.mkdir(exist_ok=True)
    account_file = cookies_dir / f"{uuid_v1}.json"
    _push_wechatmp_debug_to_status_queue(
        status_queue,
        "legacy_login_start",
        f"account={id};account_file={account_file.name}",
    )

    result = await mainline_wechatmp_cookie_gen(
        str(account_file),
        qrcode_callback=lambda qrcode_info: _push_wechatmp_qrcode_to_status_queue(
            qrcode_info, status_queue
        ),
        # 公众号登录与视频号一样更依赖真实浏览器环境，这里统一强制有头模式。
        headless=False,
    )

    _push_wechatmp_debug_to_status_queue(
        status_queue,
        "legacy_login_result",
        (
            f"success={bool(result.get('success'))};status={result.get('status')};"
            f"message={result.get('message')}"
        ),
    )

    if not result.get("success"):
        _push_login_error(status_queue, result.get("message", "微信公众号登录失败"))
        return None

    _save_user_info_record(6, account_file.name, id)
    status_queue.put("200")
    return account_file

# 快手登录
async def get_ks_cookie(id,status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        _save_user_info_record(4, f"{uuid_v1}.json", id)
        status_queue.put("200")

# 小红书登录
async def xiaohongshu_cookie_gen(id,status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        _save_user_info_record(1, f"{uuid_v1}.json", id)
        status_queue.put("200")

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
