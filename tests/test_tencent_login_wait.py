import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.DEBUG_MODE = True
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
sys.modules.setdefault("conf", conf_stub)

logger_stub = types.SimpleNamespace(
    info=lambda *_args, **_kwargs: None,
    success=lambda *_args, **_kwargs: None,
    warning=lambda *_args, **_kwargs: None,
    error=lambda *_args, **_kwargs: None,
    exception=lambda *_args, **_kwargs: None,
)
utils_log_stub = types.ModuleType("utils.log")
utils_log_stub.tencent_logger = logger_stub
utils_log_stub.bilibili_logger = logger_stub
utils_log_stub.kuaishou_logger = logger_stub
utils_log_stub.douyin_logger = logger_stub
utils_log_stub.xhs_logger = logger_stub
utils_log_stub.wechatmp_logger = logger_stub
sys.modules.setdefault("utils.log", utils_log_stub)

base_social_media_stub = types.ModuleType("utils.base_social_media")


async def _stub_set_init_script(context):
    return context


base_social_media_stub.set_init_script = _stub_set_init_script
sys.modules.setdefault("utils.base_social_media", base_social_media_stub)

playwright_stub = types.ModuleType("playwright.async_api")
playwright_stub.async_playwright = lambda: None
playwright_stub.Error = Exception
sys.modules.setdefault("playwright.async_api", playwright_stub)

sys.modules.pop("uploader.tencent_uploader.main", None)

from uploader.tencent_uploader.main import TENCENT_UPLOAD_URL, _wait_for_tencent_login


class _FakePage:
    """模拟最小页面对象，验证登录轮询阶段的主动探测行为。"""

    def __init__(self):
        self.url = "https://channels.weixin.qq.com"
        self.goto_calls: list[str] = []

    @property
    def first(self):
        return self

    def locator(self, _selector):
        return self

    async def count(self):
        return 0

    async def is_visible(self):
        return False

    async def goto(self, url: str):
        self.goto_calls.append(url)
        self.url = url


class _FakeContext:
    """模拟登录时使用的浏览器上下文。"""

    def __init__(self):
        self.page = _FakePage()
        self.storage_state_paths: list[str] = []

    async def new_page(self):
        return self.page

    async def storage_state(self, path: str):
        self.storage_state_paths.append(path)

    async def close(self):
        return None


class _FakeBrowser:
    """模拟浏览器对象，记录 context 创建行为。"""

    def __init__(self, context: _FakeContext):
        self.context = context

    async def new_context(self):
        return self.context

    async def close(self):
        return None


class _FakeChromium:
    """模拟 chromium launcher。"""

    def __init__(self, browser: _FakeBrowser):
        self.browser = browser
        self.launch_calls: list[dict] = []

    async def launch(self, **kwargs):
        self.launch_calls.append(kwargs)
        return self.browser


class _FakePlaywrightManager:
    """模拟 async_playwright 上下文管理器。"""

    def __init__(self, chromium: _FakeChromium):
        self.playwright = types.SimpleNamespace(chromium=chromium)

    async def __aenter__(self):
        return self.playwright

    async def __aexit__(self, exc_type, exc, tb):
        return None


class TencentLoginWaitTests(unittest.TestCase):
    """验证视频号登录轮询在特殊页面状态下的行为。"""

    def test_wait_for_login_does_not_probe_upload_page_when_qrcode_disappears(self):
        """二维码区域消失但未命中已扫码文案时，应保持被动等待，避免主动跳页打断登录。"""

        page = _FakePage()

        with patch(
            "uploader.tencent_uploader.main.asyncio.sleep",
            new=AsyncMock(),
        ):
            result = asyncio.run(
                _wait_for_tencent_login(
                    page=page,
                    account_file="account.json",
                    qrcode_info={"image_path": "qrcode.png", "image_data_url": "data:image/png;base64,abc"},
                    status_callback=AsyncMock(),
                    poll_interval=0,
                    max_checks=1,
                )
            )

        self.assertFalse(result["success"])
        self.assertEqual(page.goto_calls, [])

    def test_tencent_cookie_gen_applies_stealth_init_script_before_login(self):
        """视频号登录应先注入 stealth 脚本，再进入二维码登录流程。"""

        fake_context = _FakeContext()
        fake_browser = _FakeBrowser(fake_context)
        fake_chromium = _FakeChromium(fake_browser)
        fake_manager = _FakePlaywrightManager(fake_chromium)

        async def fake_set_init_script(context):
            return context

        with patch(
            "uploader.tencent_uploader.main.async_playwright",
            return_value=fake_manager,
        ), patch(
            "uploader.tencent_uploader.main.set_init_script",
            new=AsyncMock(side_effect=fake_set_init_script),
        ) as mock_set_init_script, patch(
            "uploader.tencent_uploader.main._save_tencent_qrcode",
            new=AsyncMock(return_value={"image_path": "qrcode.png", "image_data_url": "data:image/png;base64,abc"}),
        ), patch(
            "uploader.tencent_uploader.main._wait_for_tencent_login",
            new=AsyncMock(
                return_value={
                    "success": True,
                    "status": "success",
                    "message": "ok",
                    "account_file": "account.json",
                    "qrcode": {"image_path": "qrcode.png"},
                    "current_url": TENCENT_UPLOAD_URL,
                }
            ),
        ), patch(
            "uploader.tencent_uploader.main.cookie_auth",
            new=AsyncMock(return_value=True),
        ), patch(
            "uploader.tencent_uploader.main.asyncio.sleep",
            new=AsyncMock(),
        ), patch(
            "uploader.tencent_uploader.main._get_qrcode_utils",
            return_value={"remove_qrcode_file": lambda _path: False},
        ):
            tencent_main = importlib.import_module("uploader.tencent_uploader.main")
            result = asyncio.run(
                tencent_main.tencent_cookie_gen(
                    "account.json",
                    headless=True,
                )
            )

        self.assertTrue(result["success"])
        mock_set_init_script.assert_awaited_once_with(fake_context)


if __name__ == "__main__":
    unittest.main()
