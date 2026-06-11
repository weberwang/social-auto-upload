import asyncio
import sys
import types
import unittest
from pathlib import Path


conf_stub = types.ModuleType("conf")
conf_stub.BASE_DIR = Path(".")
conf_stub.LOCAL_CHROME_HEADLESS = True
conf_stub.LOCAL_CHROME_PATH = ""
sys.modules.setdefault("conf", conf_stub)

segno_stub = types.ModuleType("segno")
segno_stub.make = lambda *_args, **_kwargs: types.SimpleNamespace(save=lambda *a, **k: None)
sys.modules.setdefault("segno", segno_stub)

auth_stub = types.ModuleType("myUtils.auth")


async def _stub_check_cookie(*_args, **_kwargs):
    """测试里不真正触发账号校验。"""

    return True


auth_stub.check_cookie = _stub_check_cookie
sys.modules.setdefault("myUtils.auth", auth_stub)

bili_bridge_stub = types.ModuleType("myUtils.bilibili_web_bridge")
bili_bridge_stub.build_biliup_account_payload = lambda *_args, **_kwargs: {}
sys.modules.setdefault("myUtils.bilibili_web_bridge", bili_bridge_stub)

base_social_media_stub = types.ModuleType("utils.base_social_media")


async def _stub_set_init_script(context):
    """测试里保持上下文原样返回。"""

    return context


base_social_media_stub.set_init_script = _stub_set_init_script
sys.modules.setdefault("utils.base_social_media", base_social_media_stub)

playwright_stub = types.ModuleType("playwright.async_api")
playwright_stub.async_playwright = lambda: None
sys.modules.setdefault("playwright.async_api", playwright_stub)

logger_stub = types.SimpleNamespace(
    info=lambda *_args, **_kwargs: None,
    success=lambda *_args, **_kwargs: None,
    warning=lambda *_args, **_kwargs: None,
    error=lambda *_args, **_kwargs: None,
    exception=lambda *_args, **_kwargs: None,
)
utils_log_stub = types.ModuleType("utils.log")
utils_log_stub.bilibili_logger = logger_stub
sys.modules.setdefault("utils.log", utils_log_stub)

douyin_stub = types.ModuleType("uploader.douyin_uploader.main")
douyin_stub.douyin_cookie_gen = None
sys.modules.setdefault("uploader.douyin_uploader.main", douyin_stub)

tencent_stub = types.ModuleType("uploader.tencent_uploader.main")
tencent_stub.get_tencent_cookie = None
sys.modules.setdefault("uploader.tencent_uploader.main", tencent_stub)

wechatmp_stub = types.ModuleType("uploader.wechatmp_uploader.main")
wechatmp_stub.get_wechatmp_cookie = None
sys.modules.setdefault("uploader.wechatmp_uploader.main", wechatmp_stub)

import myUtils.login as legacy_login


class _MemoryQueue:
    """收集登录调试消息，便于断言 SSE 推送顺序。"""

    def __init__(self):
        self.items = []

    def put(self, item):
        self.items.append(item)


class WechatMpLoginDebugQueueTests(unittest.TestCase):
    """验证公众号二维码调试信息会通过历史 Web SSE 队列透传。"""

    def test_push_wechatmp_qrcode_to_status_queue_emits_debug_and_image_payload(self):
        """透传二维码时应先发调试日志，再发真正的二维码 data URL。"""

        queue = _MemoryQueue()

        asyncio.run(
            legacy_login._push_wechatmp_qrcode_to_status_queue(
                {
                    "image_data_url": "data:image/png;base64,wechatmp",
                    "image_path": "wechatmp_qrcode.png",
                    "payload_length": 31,
                    "image_byte_size": 18,
                },
                queue,
            )
        )

        self.assertEqual(
            queue.items,
            [
                "LOG:微信公众号:qr_ready:path=wechatmp_qrcode.png;payload_length=31;image_bytes=18",
                "data:image/png;base64,wechatmp",
            ],
        )
