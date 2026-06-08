import unittest
from unittest.mock import AsyncMock, patch

from uploader.tencent_uploader.main import TencentNote


class TencentNotePublishTests(unittest.IsolatedAsyncioTestCase):
    """验证视频号图文上传链路已经从占位实现切换为真实调用顺序。"""

    async def test_upload_note_content_calls_mode_switch_upload_and_fill(self):
        app = TencentNote(
            image_paths=["1.png", "2.png"],
            title="图文标题",
            note="图文正文",
            tags=["旅行"],
            publish_date=0,
            account_file="cookies/tencent.json",
        )
        page = object()

        with patch.object(app, "switch_to_note_mode", new=AsyncMock()) as mock_switch, patch.object(
            app, "upload_note_images", new=AsyncMock()
        ) as mock_upload, patch.object(app, "prepare_note_for_publish", new=AsyncMock()) as mock_prepare:
            await app.upload_note_content(page)

        mock_switch.assert_awaited_once_with(page)
        mock_upload.assert_awaited_once_with(page)
        mock_prepare.assert_awaited_once_with(page)

    async def test_prepare_note_for_publish_uses_named_collection_and_original_gate(self):
        app = TencentNote(
            image_paths=["1.png"],
            title="图文标题",
            note="图文正文",
            tags=["旅行"],
            publish_date=0,
            account_file="cookies/tencent.json",
        )
        app.collection_name = "旅行合集"
        app.declare_original = True
        app.original_type = "生活"
        page = object()

        with patch.object(app, "fill_note_title_and_tags", new=AsyncMock()) as mock_fill_title, patch.object(
            app, "fill_note_body", new=AsyncMock()
        ) as mock_fill_body, patch(
            "uploader.tencent_uploader.main.apply_tencent_named_collection",
            new=AsyncMock(),
        ) as mock_apply_collection, patch.object(
            app,
            "apply_original_statement",
            new=AsyncMock(),
        ) as mock_apply_original:
            await app.prepare_note_for_publish(page)

        mock_fill_title.assert_awaited_once_with(page)
        mock_fill_body.assert_awaited_once_with(page)
        mock_apply_collection.assert_awaited_once_with(page, "旅行合集")
        mock_apply_original.assert_awaited_once_with(page)
        self.assertEqual(app.category, "生活")
