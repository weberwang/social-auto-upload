# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import base64
import inspect
import os
from pathlib import Path
from typing import Final

from patchright.async_api import Error as PatchrightError
from patchright.async_api import Page
from patchright.async_api import Playwright
from patchright.async_api import async_playwright

from conf import BASE_DIR, DEBUG_MODE, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from uploader.base_video import BaseVideoUploader
from utils.base_social_media import set_init_script
from utils.log import wechatmp_logger

WECHATMP_LOGIN_URL: Final[str] = "https://mp.weixin.qq.com/"
WECHATMP_HOME_URL: Final[str] = "https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN"
WECHATMP_DRAFT_URL: Final[str] = (
    "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&type=10&isNew=1&lang=zh_CN"
)
WECHATMP_LOGIN_QRCODE_SELECTORS: Final[tuple[str, ...]] = (
    "img.login__type__container__scan__qrcode",
    "img[src*='qrcode']",
)
WECHATMP_LOGIN_MARKER_SELECTORS: Final[tuple[str, ...]] = (
    "div.login__type__container__scan",
    "div.login_frame.input_login",
    "img.login__type__container__scan__qrcode",
)
WECHATMP_LOGIN_SUCCESS_HINT_SELECTORS: Final[tuple[str, ...]] = (
    "h2.login__type__container__scan__info__title:has-text('扫码成功')",
    "p.login__type__container__scan__info__desc:has-text('请在微信中确认账号登录')",
)
WECHATMP_LOGIN_EXPIRED_SELECTORS: Final[tuple[str, ...]] = (
    "p.login__type__container__scan_mask__info:has-text('二维码已过期')",
    "p.login__type__container__scan_mask__info:has-text('二维码加载失败')",
)
WECHATMP_EDITOR_READY_SELECTORS: Final[tuple[str, ...]] = (
    "button:has-text('保存草稿')",
    "button:has-text('保存为草稿')",
    "div[contenteditable='true'][data-placeholder*='标题']",
    "textarea[placeholder*='标题']",
)
WECHATMP_SAVE_DRAFT_SELECTORS: Final[tuple[str, ...]] = (
    "button:has-text('保存草稿')",
    "button:has-text('保存为草稿')",
    "a:has-text('保存草稿')",
)
WECHATMP_TITLE_SELECTORS: Final[tuple[str, ...]] = (
    "textarea[placeholder*='标题']",
    "input[placeholder*='标题']",
    "div[contenteditable='true'][data-placeholder*='标题']",
)
WECHATMP_BODY_SELECTORS: Final[tuple[str, ...]] = (
    "div[contenteditable='true'][data-placeholder*='正文']",
    "div[contenteditable='true'][data-placeholder*='请输入正文']",
    "div[role='textbox'][contenteditable='true']",
    "div[contenteditable='true'].ql-editor",
)
WECHATMP_IMAGE_INPUT_SELECTORS: Final[tuple[str, ...]] = (
    "input[type='file'][accept*='image']",
    "input[type='file'][accept*='png']",
    "input[type='file']",
)
WECHATMP_SAVE_SUCCESS_SELECTORS: Final[tuple[str, ...]] = (
    "text=保存成功",
    "text=草稿保存成功",
)


def _msg(emoji: str, text: str) -> str:
    """统一公众号日志消息格式，便于和现有 uploader 输出保持一致。"""

    return f"{emoji} {text}"


def _build_login_result(
    success: bool,
    status: str,
    message: str,
    account_file: str,
    qrcode: dict | None = None,
    current_url: str = "",
) -> dict[str, object]:
    """统一返回登录结果结构，避免历史 Web、CLI 和主线各自拼字段。"""

    return {
        "success": success,
        "status": status,
        "message": message,
        "account_file": str(account_file),
        "qrcode": qrcode,
        "current_url": current_url,
    }


def _build_launch_kwargs(headless: bool) -> dict[str, object]:
    """统一浏览器启动参数，优先复用用户自定义的本地 Chrome。"""

    launch_kwargs: dict[str, object] = {"headless": headless}
    if LOCAL_CHROME_PATH:
        launch_kwargs["executable_path"] = LOCAL_CHROME_PATH
    else:
        launch_kwargs["channel"] = "chrome"
    return launch_kwargs


def _get_qrcode_utils() -> dict[str, object]:
    """延迟加载二维码工具，避免普通导入时拉起图像处理依赖。"""

    from utils.login_qrcode import build_login_qrcode_path
    from utils.login_qrcode import remove_qrcode_file

    return {
        "build_login_qrcode_path": build_login_qrcode_path,
        "remove_qrcode_file": remove_qrcode_file,
    }


async def _emit_qrcode_callback(qrcode_callback, payload: dict[str, object]) -> None:
    """兼容同步/异步二维码回调，便于旧 Web 和 CLI 复用同一主线逻辑。"""

    if not qrcode_callback:
        return
    callback_result = qrcode_callback(payload)
    if inspect.isawaitable(callback_result):
        await callback_result


async def _has_visible_selector(page: Page, selectors: tuple[str, ...]) -> bool:
    """检查候选选择器里是否存在可见元素，用于稳住页面状态探测。"""

    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible():
                return True
        except PatchrightError:
            continue
    return False


async def _click_first_visible(page: Page, selectors: tuple[str, ...]) -> bool:
    """点击首个可见候选元素，避免页面小改版后单一选择器整条链路失效。"""

    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible():
                await locator.click()
                return True
        except PatchrightError:
            continue
    return False


async def _fill_first_visible(page: Page, selectors: tuple[str, ...], value: str) -> bool:
    """向首个可见输入控件写值，并在 contenteditable 场景下回退到键盘输入。"""

    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if not await locator.count() or not await locator.is_visible():
                continue
            await locator.click()
            tag_name = await locator.evaluate("node => node.tagName.toLowerCase()")
            if tag_name in {"input", "textarea"}:
                await locator.fill(value)
            else:
                await locator.evaluate("(node, text) => { node.innerHTML = ''; node.textContent = text; }", value)
            return True
        except PatchrightError:
            continue
    return False


async def _ensure_scan_mode(page: Page) -> None:
    """公众号登录页默认可能停在账号密码登录，这里统一切到扫码模式。"""

    scan_switch = page.locator("a.login__type__container__select-type__scan").first
    if await scan_switch.count():
        await scan_switch.click()
        await asyncio.sleep(1)


async def _capture_qrcode_locator(locator, output_path: Path) -> dict[str, str]:
    """把二维码元素截图成文件和 data URL，统一供前端与终端复用。"""

    image_bytes = await locator.screenshot(type="png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {
        "image_path": str(output_path),
        "image_data_url": f"data:image/png;base64,{encoded}",
    }


async def _save_wechatmp_qrcode(
    page: Page,
    account_file: str,
    previous_qrcode_path: Path | None = None,
    qrcode_callback=None,
) -> dict[str, str]:
    """截图保存公众号登录二维码，并把可展示结果回调给上层。"""

    await _ensure_scan_mode(page)
    qrcode_locator = page.locator(WECHATMP_LOGIN_QRCODE_SELECTORS[0]).first
    if not await qrcode_locator.count():
        for selector in WECHATMP_LOGIN_QRCODE_SELECTORS[1:]:
            candidate = page.locator(selector).first
            if await candidate.count():
                qrcode_locator = candidate
                break

    await qrcode_locator.wait_for(state="visible", timeout=30_000)
    qrcode_utils = _get_qrcode_utils()
    qrcode_path = qrcode_utils["build_login_qrcode_path"](account_file, suffix="wechatmp_login_qrcode")
    if previous_qrcode_path and previous_qrcode_path.exists():
        previous_qrcode_path.unlink()
    qrcode_info = await _capture_qrcode_locator(qrcode_locator, qrcode_path)
    await _emit_qrcode_callback(qrcode_callback, qrcode_info)
    wechatmp_logger.info(_msg("🖼️", f"二维码已经准备好啦，已保存到: {qrcode_path}"))
    return qrcode_info


async def _is_wechatmp_login_completed(page: Page) -> bool:
    """通过 URL 和登录区可见性联合判断公众号扫码是否已经完成。"""

    if page.url.startswith("https://mp.weixin.qq.com/cgi-bin/"):
        return True
    if await _has_visible_selector(page, WECHATMP_LOGIN_MARKER_SELECTORS):
        return False
    return not page.url.startswith(WECHATMP_LOGIN_URL)


async def _is_wechatmp_qrcode_expired(page: Page) -> bool:
    """判断公众号登录二维码是否已经过期或加载失败。"""

    return await _has_visible_selector(page, WECHATMP_LOGIN_EXPIRED_SELECTORS)


async def _refresh_wechatmp_qrcode(page: Page) -> None:
    """刷新过期二维码，兼容当前登录页上的“点击刷新/重新扫码”入口。"""

    refreshed = await _click_first_visible(
        page,
        (
            "a:has-text('点击刷新')",
            "a:has-text('重新扫码')",
        ),
    )
    if not refreshed:
        raise RuntimeError("当前页面没有找到公众号二维码刷新入口")
    await asyncio.sleep(1)


async def cookie_auth(account_file: str | Path) -> bool:
    """校验公众号 Cookie 是否仍然有效，失效时统一返回 False。"""

    account_path = Path(account_file)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_build_launch_kwargs(headless=True))
        try:
            context = await browser.new_context(storage_state=str(account_path))
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto(WECHATMP_HOME_URL)
            await page.wait_for_timeout(2_000)
            if await _has_visible_selector(page, WECHATMP_LOGIN_MARKER_SELECTORS):
                wechatmp_logger.info(_msg("🥹", "cookie 已失效，得重新登录一下"))
                return False
            wechatmp_logger.success(_msg("🥳", "cookie 有效"))
            return True
        except (OSError, PatchrightError) as exc:
            wechatmp_logger.warning(_msg("😵", f"cookie 校验时出错，按失效处理: {exc}"))
            return False
        finally:
            await browser.close()


async def wechatmp_setup(
    account_file: str,
    handle: bool = False,
    return_detail: bool = False,
    qrcode_callback=None,
    headless: bool = LOCAL_CHROME_HEADLESS,
):
    """统一处理公众号 cookie 复用与重新登录。"""

    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            result = _build_login_result(False, "cookie_invalid", "cookie文件不存在或已失效", account_file)
            return result if return_detail else False
        wechatmp_logger.info(_msg("🥹", "cookie 失效了，准备打开浏览器重新登录微信公众号"))
        result = await wechatmp_cookie_gen(
            account_file,
            qrcode_callback=qrcode_callback,
            headless=headless,
        )
        return result if return_detail else result["success"]

    result = _build_login_result(True, "cookie_valid", "cookie有效", account_file)
    return result if return_detail else True


async def wechatmp_cookie_gen(
    account_file: str,
    qrcode_callback=None,
    poll_interval: int = 2,
    max_checks: int = 120,
    headless: bool = LOCAL_CHROME_HEADLESS,
) -> dict[str, object]:
    """执行公众号扫码登录，并把二维码结果统一回调给上层。"""

    account_path = Path(account_file)
    account_path.parent.mkdir(parents=True, exist_ok=True)
    qrcode_utils = _get_qrcode_utils()
    if headless:
        wechatmp_logger.info(_msg("🖼️", "公众号登录将以无头模式运行，小人会输出二维码截图给上层展示"))

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**_build_launch_kwargs(headless=headless))
        context = await browser.new_context()
        context = await set_init_script(context)
        qrcode_path: Path | None = None
        qrcode_info: dict[str, str] | None = None
        result = _build_login_result(False, "failed", "微信公众号登录失败", account_file)
        try:
            page = await context.new_page()
            await page.goto(WECHATMP_LOGIN_URL)
            qrcode_info = await _save_wechatmp_qrcode(page, account_file, qrcode_callback=qrcode_callback)
            qrcode_path = Path(qrcode_info["image_path"])
            wechatmp_logger.info(_msg("🧍", "请扫码，小人正在耐心等待公众号登录完成"))

            for _ in range(max_checks):
                if await _is_wechatmp_login_completed(page):
                    await asyncio.sleep(2)
                    await context.storage_state(path=str(account_path))
                    if await cookie_auth(str(account_path)):
                        wechatmp_logger.success(_msg("🥳", "微信公众号扫码登录成功，小人开心收工"))
                        result = _build_login_result(
                            True,
                            "success",
                            "微信公众号扫码登录成功",
                            account_file,
                            qrcode_info,
                            page.url,
                        )
                    else:
                        result = _build_login_result(
                            False,
                            "cookie_invalid",
                            "微信公众号扫码流程结束，但 cookie 校验失败",
                            account_file,
                            qrcode_info,
                            page.url,
                        )
                    return result

                if await _is_wechatmp_qrcode_expired(page):
                    wechatmp_logger.warning(_msg("😵", "二维码失效了，小人马上去刷新"))
                    await _refresh_wechatmp_qrcode(page)
                    qrcode_info = await _save_wechatmp_qrcode(
                        page,
                        account_file,
                        previous_qrcode_path=qrcode_path,
                        qrcode_callback=qrcode_callback,
                    )
                    qrcode_path = Path(qrcode_info["image_path"])

                await asyncio.sleep(poll_interval)

            result = _build_login_result(
                False,
                "timeout",
                "等待微信公众号扫码登录超时",
                account_file,
                qrcode_info,
                page.url,
            )
        except (OSError, PatchrightError) as exc:
            result = _build_login_result(
                False,
                "failed",
                str(exc),
                account_file,
                qrcode_info,
                current_url=page.url if "page" in locals() else "",
            )
        finally:
            if qrcode_path and qrcode_utils["remove_qrcode_file"](qrcode_path):
                wechatmp_logger.info(_msg("🧹", f"临时二维码文件已清理: {qrcode_path}"))
            if not result["success"]:
                wechatmp_logger.error(_msg("😢", f"登录失败: {result['message']}"))
            await context.close()
            await browser.close()
        return result


async def get_wechatmp_cookie(
    account_file: str,
    qrcode_callback=None,
    headless: bool = LOCAL_CHROME_HEADLESS,
) -> dict[str, object]:
    """兼容旧命名，供桥接层直接调用公众号扫码登录主线。"""

    return await wechatmp_cookie_gen(
        account_file,
        qrcode_callback=qrcode_callback,
        headless=headless,
    )


class WeChatMpArticle(BaseVideoUploader):
    """封装微信公众号图文草稿保存流程。"""

    def __init__(
        self,
        image_paths: list[str],
        title: str,
        note: str,
        tags: list[str],
        account_file: str,
        debug: bool = DEBUG_MODE,
        headless: bool = LOCAL_CHROME_HEADLESS,
    ) -> None:
        self.image_paths = image_paths
        self.title = title
        self.note = note
        self.tags = tags
        self.account_file = str(account_file)
        self.debug = debug
        self.headless = headless

    async def validate_upload_args(self) -> None:
        """在真正打开页面前先校验 cookie、标题、正文和图片。"""

        if not os.path.exists(self.account_file):
            raise RuntimeError(f"cookie文件不存在，请先完成微信公众号登录: {self.account_file}")
        if not await cookie_auth(self.account_file):
            raise RuntimeError(f"cookie文件已失效，请先完成微信公众号登录: {self.account_file}")
        if not self.title.strip():
            raise ValueError("微信公众号图文发布时，title 是必须的")
        if not self.note.strip():
            raise ValueError("微信公众号图文发布时，note 是必须的")
        if not self.image_paths:
            raise ValueError("微信公众号图文发布时，图片是必须的")

        self.image_paths = [str(self.validate_image_file(path)) for path in self.image_paths]

    def _build_body_text(self) -> str:
        """把正文和标签统一拼成编辑器可直接写入的文案。"""

        tag_lines = [f"#{tag}" for tag in self.tags if tag]
        if not tag_lines:
            return self.note.strip()
        return f"{self.note.strip()}\n\n{' '.join(tag_lines)}"

    async def _wait_editor_ready(self, page: Page) -> None:
        """等待公众号图文编辑器加载完成，并在仍停留登录页时直接失败。"""

        for _ in range(30):
            if await _has_visible_selector(page, WECHATMP_EDITOR_READY_SELECTORS):
                return
            if await _has_visible_selector(page, WECHATMP_LOGIN_MARKER_SELECTORS):
                raise RuntimeError("公众号图文页仍停留在登录页，请确认账号 cookie 是否有效")
            await asyncio.sleep(1)
        raise RuntimeError("等待公众号图文编辑器加载超时")

    async def _upload_images(self, page: Page) -> None:
        """尝试通过通用图片上传输入框插入文章图片，优先一次性上传全部图片。"""

        for selector in WECHATMP_IMAGE_INPUT_SELECTORS:
            locator = page.locator(selector).first
            try:
                if not await locator.count():
                    continue
                await locator.set_input_files(self.image_paths)
                await asyncio.sleep(2)
                return
            except PatchrightError:
                continue
        wechatmp_logger.warning(_msg("📭", "当前页面未识别到图片上传输入框，小人先继续保存纯正文草稿"))

    async def _fill_article(self, page: Page) -> None:
        """填充图文标题、正文，并尽量补齐图片素材。"""

        filled_title = await _fill_first_visible(page, WECHATMP_TITLE_SELECTORS, self.title.strip())
        if not filled_title:
            raise RuntimeError("未找到微信公众号图文标题输入框")

        filled_body = await _fill_first_visible(page, WECHATMP_BODY_SELECTORS, self._build_body_text())
        if not filled_body:
            raise RuntimeError("未找到微信公众号图文正文编辑区")

        await self._upload_images(page)

    async def _save_draft(self, page: Page) -> None:
        """点击保存草稿，并尽量等待成功提示出现。"""

        saved = await _click_first_visible(page, WECHATMP_SAVE_DRAFT_SELECTORS)
        if not saved:
            raise RuntimeError("未找到微信公众号保存草稿按钮")

        for _ in range(15):
            if await _has_visible_selector(page, WECHATMP_SAVE_SUCCESS_SELECTORS):
                wechatmp_logger.success(_msg("🥳", "公众号图文草稿保存成功"))
                return
            await asyncio.sleep(1)

        wechatmp_logger.warning(_msg("😵", "未捕获到明确的草稿保存成功提示，请人工确认当前页面结果"))

    async def upload(self, playwright: Playwright) -> None:
        """打开公众号图文编辑页并执行草稿保存。"""

        browser = await playwright.chromium.launch(**_build_launch_kwargs(headless=self.headless))
        context = await browser.new_context(storage_state=self.account_file)
        context = await set_init_script(context)
        try:
            page = await context.new_page()
            await page.goto(WECHATMP_DRAFT_URL)
            await self._wait_editor_ready(page)
            await self._fill_article(page)
            await self._save_draft(page)
            await context.storage_state(path=self.account_file)
            wechatmp_logger.info(_msg("🥳", "cookie 更新完毕"))
        finally:
            await context.close()
            await browser.close()

    async def main(self) -> None:
        """执行公众号图文上传主流程。"""

        await self.validate_upload_args()
        async with async_playwright() as playwright:
            await self.upload(playwright)
