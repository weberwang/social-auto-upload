from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class PlatformLoginRequest:
    """描述一次平台登录请求。"""

    platform: str
    account_name: str
    headless: bool = True


@dataclass(slots=True)
class PlatformCheckRequest:
    """描述一次平台账号校验请求。"""

    platform: str
    account_name: str


@dataclass(slots=True)
class UploadVideoRequest:
    """描述一次跨平台视频上传请求。"""

    platform: str
    account_name: str
    file: Path
    title: str
    desc: str
    tags: list[str]
    schedule: datetime | int
    extra: dict[str, object] | None = None
