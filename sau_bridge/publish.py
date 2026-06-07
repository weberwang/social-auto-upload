from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PublishVideoPayload:
    """描述一次视频发布 bridge 请求。"""

    platform: str
    account_name: str
    file_path: Path
    title: str
    description: str
    tags: list[str]
    schedule: str | None = None
    tid: int | None = None


@dataclass(frozen=True, slots=True)
class PublishNotePayload:
    """描述一次图文发布 bridge 请求。"""

    platform: str
    account_name: str
    image_files: list[Path]
    title: str
    note: str
    tags: list[str]
    schedule: str | None = None


def _require_non_empty_string(field_name: str, value: object) -> str:
    """把 bridge 输入约束为非空文本。"""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _parse_tags(raw_tags: object) -> list[str]:
    """把 tags 解析成字符串列表，避免后续上传函数重复做边界判断。"""

    if raw_tags is None:
        return []
    if not isinstance(raw_tags, list) or not all(isinstance(item, str) for item in raw_tags):
        raise ValueError("tags must be a list of strings")
    return [item.strip() for item in raw_tags if item.strip()]


def _parse_optional_schedule(raw_schedule: object) -> str | None:
    """保留原始定时字符串；真正转换复用现有 `parse_schedule`。"""

    if raw_schedule in (None, ""):
        return None
    return _require_non_empty_string("schedule", raw_schedule)


def _parse_video_payload(payload: object) -> PublishVideoPayload:
    """把原始 JSON payload 解析为视频发布请求。"""

    if not isinstance(payload, dict):
        raise ValueError("publish-video payload must be an object")
    return PublishVideoPayload(
        platform=_require_non_empty_string("platform", payload.get("platform")),
        account_name=_require_non_empty_string("account_name", payload.get("account_name")),
        file_path=Path(_require_non_empty_string("file_path", payload.get("file_path"))),
        title=_require_non_empty_string("title", payload.get("title")),
        description=str(payload.get("description") or ""),
        tags=_parse_tags(payload.get("tags")),
        schedule=_parse_optional_schedule(payload.get("schedule")),
        tid=int(payload["tid"]) if payload.get("tid") not in (None, "") else None,
    )


def _parse_note_payload(payload: object) -> PublishNotePayload:
    """把原始 JSON payload 解析为图文发布请求。"""

    if not isinstance(payload, dict):
        raise ValueError("publish-note payload must be an object")
    raw_images = payload.get("image_files")
    if not isinstance(raw_images, list) or not raw_images:
        raise ValueError("image_files must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in raw_images):
        raise ValueError("image_files must contain non-empty strings")
    return PublishNotePayload(
        platform=_require_non_empty_string("platform", payload.get("platform")),
        account_name=_require_non_empty_string("account_name", payload.get("account_name")),
        image_files=[Path(item) for item in raw_images],
        title=_require_non_empty_string("title", payload.get("title")),
        note=_require_non_empty_string("note", payload.get("note")),
        tags=_parse_tags(payload.get("tags")),
        schedule=_parse_optional_schedule(payload.get("schedule")),
    )


async def run_publish_video(payload: object) -> dict[str, Any]:
    """执行视频发布并返回统一 bridge JSON。"""

    request = _parse_video_payload(payload)

    if request.platform == "douyin":
        from sau_cli import DouyinVideoUploadRequest, parse_schedule, upload_video

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_video(
            DouyinVideoUploadRequest(
                account_name=request.account_name,
                video_file=request.file_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "kuaishou":
        from sau_cli import KuaishouVideoUploadRequest, parse_schedule, upload_kuaishou_video

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_kuaishou_video(
            KuaishouVideoUploadRequest(
                account_name=request.account_name,
                video_file=request.file_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "xiaohongshu":
        from sau_cli import XiaohongshuVideoUploadRequest, parse_schedule, upload_xiaohongshu_video

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_xiaohongshu_video(
            XiaohongshuVideoUploadRequest(
                account_name=request.account_name,
                video_file=request.file_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "bilibili":
        if request.tid is None:
            raise ValueError("tid is required for bilibili video publish")
        from sau_cli import BilibiliVideoUploadRequest, parse_schedule, upload_bilibili_video

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_bilibili_video(
            BilibiliVideoUploadRequest(
                account_name=request.account_name,
                video_file=request.file_path,
                title=request.title,
                description=request.description,
                tid=request.tid,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "tencent":
        from sau_cli import TencentVideoUploadRequest, parse_schedule, upload_tencent_video

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_tencent_video(
            TencentVideoUploadRequest(
                account_name=request.account_name,
                video_file=request.file_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    else:
        raise ValueError(f"unsupported platform: {request.platform}")

    return {"success": True, "data": {"account_file": str(account_file)}}


async def run_publish_note(payload: object) -> dict[str, Any]:
    """执行图文发布并返回统一 bridge JSON。"""

    request = _parse_note_payload(payload)

    if request.platform == "douyin":
        from sau_cli import DouyinNoteUploadRequest, parse_schedule, upload_note

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_note(
            DouyinNoteUploadRequest(
                account_name=request.account_name,
                image_files=request.image_files,
                title=request.title,
                note=request.note,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "kuaishou":
        from sau_cli import KuaishouNoteUploadRequest, parse_schedule, upload_kuaishou_note

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_kuaishou_note(
            KuaishouNoteUploadRequest(
                account_name=request.account_name,
                image_files=request.image_files,
                title=request.title,
                note=request.note,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    elif request.platform == "xiaohongshu":
        from sau_cli import XiaohongshuNoteUploadRequest, parse_schedule, upload_xiaohongshu_note

        publish_date = parse_schedule(request.schedule) if request.schedule else 0
        account_file = await upload_xiaohongshu_note(
            XiaohongshuNoteUploadRequest(
                account_name=request.account_name,
                image_files=request.image_files,
                title=request.title,
                note=request.note,
                tags=request.tags,
                publish_date=publish_date,
            )
        )
    else:
        raise ValueError(f"unsupported note platform: {request.platform}")

    return {"success": True, "data": {"account_file": str(account_file)}}
