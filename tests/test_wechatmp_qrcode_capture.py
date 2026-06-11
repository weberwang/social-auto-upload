import asyncio
import base64
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.DEBUG_MODE = False
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
sys.modules.setdefault("conf", conf_stub)

patchright_stub = types.ModuleType("patchright.async_api")
patchright_stub.Error = Exception
patchright_stub.Page = object
patchright_stub.Playwright = object
patchright_stub.async_playwright = lambda: None
sys.modules.setdefault("patchright.async_api", patchright_stub)

base_video_stub = types.ModuleType("uploader.base_video")


class _BaseVideoUploader:
    """测试用 uploader 基类桩，避免导入真实上传依赖。"""


base_video_stub.BaseVideoUploader = _BaseVideoUploader
sys.modules.setdefault("uploader.base_video", base_video_stub)

base_social_media_stub = types.ModuleType("utils.base_social_media")


async def _stub_set_init_script(context):
    """测试里保持 context 原样返回。"""

    return context


base_social_media_stub.set_init_script = _stub_set_init_script
sys.modules.setdefault("utils.base_social_media", base_social_media_stub)

logger_stub = types.SimpleNamespace(
    info=lambda *_args, **_kwargs: None,
    success=lambda *_args, **_kwargs: None,
    warning=lambda *_args, **_kwargs: None,
    error=lambda *_args, **_kwargs: None,
)
utils_log_stub = types.ModuleType("utils.log")
utils_log_stub.wechatmp_logger = logger_stub
utils_log_stub.bilibili_logger = logger_stub
utils_log_stub.tencent_logger = logger_stub
utils_log_stub.kuaishou_logger = logger_stub
utils_log_stub.douyin_logger = logger_stub
utils_log_stub.xhs_logger = logger_stub
sys.modules.setdefault("utils.log", utils_log_stub)

from uploader.wechatmp_uploader import main as wechatmp_main


class _FakeQrLocator:
    """模拟公众号二维码元素，支持“先可见、后加载完成”的状态切换。"""

    def __init__(self, states, image_bytes: bytes):
        self._states = list(states)
        self._image_bytes = image_bytes
        self._evaluate_calls = 0

    async def evaluate(self, _script):
        """按顺序返回图片加载状态，最后一次状态会持续复用。"""

        index = min(self._evaluate_calls, len(self._states) - 1)
        self._evaluate_calls += 1
        return self._states[index]

    async def screenshot(self, type="png"):
        """只有在图片真正加载完成后才允许截图，模拟真实浏览器行为。"""

        if type != "png":
            raise AssertionError("测试仅覆盖 PNG 二维码截图路径")

        latest_state = self._states[min(max(self._evaluate_calls - 1, 0), len(self._states) - 1)]
        if not latest_state.get("complete") or latest_state.get("naturalWidth", 0) <= 0:
            raise AssertionError("二维码图片尚未加载完成时不应开始截图")
        return self._image_bytes


class _FakeSimpleLocator:
    """模拟基础 locator，覆盖扫码模式切换里用到的最小接口。"""

    def __init__(self, count: int = 0, visible: bool = False):
        self._count = count
        self._visible = visible
        self.click_calls = 0

    @property
    def first(self):
        """测试里不区分 locator 与 first，直接返回自身。"""

        return self

    async def count(self):
        """返回当前匹配节点数量。"""

        return self._count

    async def is_visible(self):
        """返回当前节点是否可见。"""

        return self._visible

    async def click(self):
        """记录点击次数，便于断言是否误点隐藏切换按钮。"""

        self.click_calls += 1


class _FakeScanModePage:
    """模拟公众号登录页，只暴露扫码模式判断所需的 locator 能力。"""

    def __init__(self, *, scan_switch_locator: _FakeSimpleLocator, qrcode_locator: _FakeSimpleLocator):
        self._scan_switch_locator = scan_switch_locator
        self._qrcode_locator = qrcode_locator

    def locator(self, selector: str):
        """按选择器名返回对应的测试 locator。"""

        if selector == "a.login__type__container__select-type__scan":
            return self._scan_switch_locator
        if selector == wechatmp_main.WECHATMP_LOGIN_QRCODE_SELECTORS[0]:
            return self._qrcode_locator
        return _FakeSimpleLocator()


class WechatMpQrcodeCaptureTests(unittest.IsolatedAsyncioTestCase):
    """验证公众号二维码采集会等待图片真正加载完成，避免前端拿到空白图。"""

    async def test_capture_qrcode_locator_waits_until_image_is_loaded(self):
        """二维码元素先可见后解码完成时，应等待 `complete/naturalWidth` 就绪后再截图。"""

        tmp_dir = Path(tempfile.mkdtemp())
        output_path = tmp_dir / "wechatmp_qrcode.png"
        locator = _FakeQrLocator(
            states=[
                {"complete": False, "naturalWidth": 0, "naturalHeight": 0},
                {"complete": False, "naturalWidth": 0, "naturalHeight": 0},
                {"complete": True, "naturalWidth": 472, "naturalHeight": 472},
            ],
            image_bytes=b"wechatmp-qrcode",
        )

        try:
            with patch.object(wechatmp_main.asyncio, "sleep", new=AsyncMock()) as mock_sleep:
                result = await wechatmp_main._capture_qrcode_locator(locator, output_path)

            self.assertEqual(result["image_path"], str(output_path))
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), b"wechatmp-qrcode")
            self.assertEqual(
                result["image_data_url"],
                f"data:image/png;base64,{base64.b64encode(b'wechatmp-qrcode').decode('ascii')}",
            )
            self.assertEqual(locator._evaluate_calls, 3)
            self.assertEqual(mock_sleep.await_count, 2)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    async def test_ensure_scan_mode_skips_hidden_switch_when_qrcode_is_already_visible(self):
        """页面已在扫码态时，不应继续点击隐藏的扫码切换按钮。"""

        scan_switch_locator = _FakeSimpleLocator(count=1, visible=False)
        qrcode_locator = _FakeSimpleLocator(count=1, visible=True)
        page = _FakeScanModePage(
            scan_switch_locator=scan_switch_locator,
            qrcode_locator=qrcode_locator,
        )

        with patch.object(wechatmp_main.asyncio, "sleep", new=AsyncMock()) as mock_sleep:
            await wechatmp_main._ensure_scan_mode(page)

        self.assertEqual(scan_switch_locator.click_calls, 0)
        self.assertEqual(mock_sleep.await_count, 0)
