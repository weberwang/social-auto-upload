from __future__ import annotations

import asyncio

from playwright.async_api import Page


NOTE_MODE_SELECTORS = (
    'div[role="tab"]:has-text("图文")',
    'div[role="tab"]:has-text("发布图文")',
    'button:has-text("图文")',
    'button:has-text("发布图文")',
    'text="图文"',
    'text="发布图文"',
)

NOTE_UPLOAD_READY_SELECTORS = (
    'button:has-text("发表")',
    'div.form-btns button:has-text("发表")',
)

NOTE_TITLE_EDITORS = (
    'div.input-editor',
    '[contenteditable="true"]',
    'textarea',
)

NOTE_BODY_EDITORS = (
    '[contenteditable="true"]',
    'textarea',
)

NOTE_COLLECTION_LABELS = (
    'text="添加到合集"',
    'text="合集"',
)


async def _click_first_visible(page: Page, selectors: tuple[str, ...]) -> bool:
    """按顺序尝试点击第一个可见入口，避免页面灰度导致单一选择器失效。"""

    for selector in selectors:
        locator = page.locator(selector).first
        try:
            if await locator.count() and await locator.is_visible():
                await locator.click()
                return True
        except Exception:
            continue
    return False


async def switch_to_tencent_note_mode(page: Page) -> None:
    """切换到视频号图文发布模式，找不到入口时立即失败，避免后续误填视频表单。"""

    switched = await _click_first_visible(page, NOTE_MODE_SELECTORS)
    if not switched:
        raise RuntimeError("未找到视频号图文发布入口")
    await page.wait_for_timeout(1000)


async def upload_tencent_note_images(page: Page, image_paths: list[str]) -> None:
    """上传图文图片，并等待页面进入可继续填写内容的状态。"""

    file_input = page.locator('input[type="file"]').first
    await file_input.set_input_files(image_paths)
    await wait_for_tencent_note_upload_ready(page)


async def fill_tencent_note_title_and_tags(page: Page, title: str, tags: list[str]) -> None:
    """填写图文标题和话题，保持与视频发布页相同的输入节奏。"""

    for selector in NOTE_TITLE_EDITORS:
        editor = page.locator(selector).first
        try:
            if await editor.count() and await editor.is_visible():
                await editor.click()
                await page.keyboard.type(title)
                await page.keyboard.press("Enter")
                for tag in tags:
                    await page.keyboard.type(f"#{tag}")
                    await page.keyboard.press("Space")
                return
        except Exception:
            continue
    raise RuntimeError("未找到视频号图文标题输入区域")


async def fill_tencent_note_body(page: Page, note: str) -> None:
    """在图文正文存在时写入正文；页面只有标题输入时跳过，不阻断发布。"""

    if not note:
        return

    for selector in NOTE_BODY_EDITORS:
        editor = page.locator(selector).first
        try:
            if await editor.count() and await editor.is_visible():
                await editor.click()
                await page.keyboard.press("End")
                await page.keyboard.press("Enter")
                await page.keyboard.type(note)
                return
        except Exception:
            continue


async def wait_for_tencent_note_upload_ready(page: Page) -> None:
    """等待图文素材上传完成，直到页面出现可发布按钮。"""

    for _ in range(30):
        if await _clickless_publish_ready(page):
            return
        await asyncio.sleep(1)
    raise RuntimeError("视频号图文图片上传超时，页面仍未进入可发布状态")


async def _clickless_publish_ready(page: Page) -> bool:
    """检查页面是否已经出现可操作的发表按钮。"""

    for selector in NOTE_UPLOAD_READY_SELECTORS:
        button = page.locator(selector).first
        try:
            if await button.count() and await button.is_visible():
                disabled_attr = await button.get_attribute("disabled")
                class_name = await button.get_attribute("class")
                return disabled_attr is None and "disabled" not in str(class_name or "")
        except Exception:
            continue
    return False


async def apply_tencent_named_collection(page: Page, collection_name: str) -> None:
    """按合集名称选择目标合集；没找到对应名称时回退到原有流程处理。"""

    if not collection_name:
        return

    opened = await _click_first_visible(page, NOTE_COLLECTION_LABELS)
    if not opened:
        return

    option = page.locator(f'text="{collection_name}"').first
    if await option.count() and await option.is_visible():
        await option.click()
