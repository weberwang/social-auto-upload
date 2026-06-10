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
sys.modules["conf"] = conf_stub

logger_stub = types.SimpleNamespace(
    info=lambda *_args, **_kwargs: None,
    success=lambda *_args, **_kwargs: None,
    warning=lambda *_args, **_kwargs: None,
    error=lambda *_args, **_kwargs: None,
    exception=lambda *_args, **_kwargs: None,
)
utils_log_stub = types.ModuleType("utils.log")
utils_log_stub.douyin_logger = logger_stub
utils_log_stub.bilibili_logger = logger_stub
utils_log_stub.tencent_logger = logger_stub
utils_log_stub.kuaishou_logger = logger_stub
utils_log_stub.xhs_logger = logger_stub
utils_log_stub.wechatmp_logger = logger_stub
sys.modules["utils.log"] = utils_log_stub

base_social_media_stub = types.ModuleType("utils.base_social_media")


async def _stub_set_init_script(context):
    return context


base_social_media_stub.set_init_script = _stub_set_init_script
sys.modules["utils.base_social_media"] = base_social_media_stub

patchright_stub = types.ModuleType("patchright.async_api")
patchright_stub.Page = object
patchright_stub.Playwright = object
patchright_stub.async_playwright = lambda: None
sys.modules["patchright.async_api"] = patchright_stub

class _FakeTextLocator:
    """模拟登录页文字定位器。"""

    async def count(self):
        return 0


class _FakePage:
    """模拟轻量页面对象，覆盖 cookie 校验需要的最小接口。"""

    def __init__(self):
        self.url = ""
        self.goto_calls: list[tuple[str, str, int]] = []

    async def goto(self, url: str, wait_until: str = "load", timeout: int = 30000):
        self.goto_calls.append((url, wait_until, timeout))
        self.url = "https://creator.douyin.com/creator-micro/home"
        raise TimeoutError("mock timeout")

    def get_by_text(self, _text: str):
        return _FakeTextLocator()


class _FakeContext:
    """模拟浏览器上下文。"""

    def __init__(self, page: _FakePage):
        self.page = page

    async def new_page(self):
        return self.page


class _FakeBrowser:
    """模拟浏览器对象。"""

    def __init__(self, context: _FakeContext):
        self.context = context

    async def new_context(self, storage_state=None):
        return self.context

    async def close(self):
        return None


class _FakeChromium:
    """模拟 chromium launcher。"""

    def __init__(self, browser: _FakeBrowser):
        self.browser = browser

    async def launch(self, **_kwargs):
        return self.browser


class _FakePlaywrightManager:
    """模拟 async_playwright 上下文管理器。"""

    def __init__(self, chromium: _FakeChromium):
        self.playwright = types.SimpleNamespace(chromium=chromium)

    async def __aenter__(self):
        return self.playwright

    async def __aexit__(self, exc_type, exc, tb):
        return None


class DouyinCookieAuthTests(unittest.TestCase):
    """验证抖音主线 cookie 校验不会因重页面慢加载误判。"""

    def test_cookie_auth_tolerates_navigation_timeout_after_reaching_creator_domain(self):
        """若已进入创作者域名，即使页面导航超时，也不应直接判 cookie 失效。"""

        sys.modules.pop("uploader.douyin_uploader.main", None)
        douyin_main = importlib.import_module("uploader.douyin_uploader.main")
        fake_page = _FakePage()
        fake_context = _FakeContext(fake_page)
        fake_browser = _FakeBrowser(fake_context)
        fake_manager = _FakePlaywrightManager(_FakeChromium(fake_browser))

        with patch(
            "uploader.douyin_uploader.main.async_playwright",
            return_value=fake_manager,
        ), patch(
            "uploader.douyin_uploader.main.set_init_script",
            new=AsyncMock(side_effect=_stub_set_init_script),
        ):
            result = asyncio.run(douyin_main.cookie_auth("account.json"))

        self.assertTrue(result)
        self.assertEqual(
            fake_page.goto_calls,
            [(douyin_main.DOUYIN_HOME_URL, "domcontentloaded", 10000)],
        )


if __name__ == "__main__":
    unittest.main()
