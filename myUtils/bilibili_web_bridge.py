from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from conf import BASE_DIR
from uploader.bilibili_uploader.runtime import run_biliup_command
from utils.files_times import generate_schedule_time_next_day
from utils.log import bilibili_logger


def _ensure_safe_file_name(file_name: str) -> str:
    """只允许使用纯文件名，避免历史 Web 路径参数越界到账号或视频目录外。"""

    normalized_name = Path(str(file_name or "")).name
    if not normalized_name or normalized_name != str(file_name):
        raise ValueError("文件名非法，必须是纯文件名")
    return normalized_name


def resolve_bilibili_account_path(account_file_name: str) -> Path:
    """兼容历史 Web `cookiesFile` 与主线 CLI `cookies` 两套 B 站账号文件目录。"""

    safe_name = _ensure_safe_file_name(account_file_name)
    legacy_path = Path(BASE_DIR / "cookiesFile" / safe_name)
    if legacy_path.exists():
        return legacy_path

    mainline_path = Path(BASE_DIR / "cookies" / safe_name)
    if mainline_path.exists():
        return mainline_path

    # 优先返回历史 Web 目录，便于上层给出更符合当前页面心智的错误提示。
    return legacy_path


def resolve_uploaded_video_path(video_file_name: str) -> Path:
    """把历史 Web 上传返回的文件名解析成磁盘路径，并限制在 `videoFile` 目录内。"""

    safe_name = _ensure_safe_file_name(video_file_name)
    return Path(BASE_DIR / "videoFile" / safe_name)


def build_biliup_account_payload(raw_payload: dict) -> dict:
    """把历史扁平账号文件转换成 biliup CLI 期望的账号结构。"""

    if not isinstance(raw_payload, dict):
        raise ValueError("B站账号文件内容非法，必须是 JSON 对象")

    if raw_payload.get("cookie_info") and raw_payload.get("token_info"):
        cookie_items = raw_payload.get("cookie_info", {}).get("cookies") or []
        token_info = raw_payload.get("token_info") or {}
    else:
        cookie_names = [
            "SESSDATA",
            "bili_jct",
            "DedeUserID",
            "DedeUserID__ckMd5",
            "sid",
            "buvid3",
            "buvid4",
        ]
        cookie_items = [
            {"name": cookie_name, "value": raw_payload[cookie_name]}
            for cookie_name in cookie_names
            if raw_payload.get(cookie_name)
        ]
        token_info = raw_payload

    if not cookie_items:
        raise ValueError("B站账号文件缺少 cookie 字段")

    cookies_by_name = {}
    for cookie in cookie_items:
        cookie_name = cookie.get("name")
        cookie_value = cookie.get("value")
        if cookie_name and cookie_value:
            cookies_by_name[cookie_name] = cookie_value

    normalized_cookies = [
        {"name": name, "value": value}
        for name, value in cookies_by_name.items()
    ]
    mid_value = token_info.get("mid") or raw_payload.get("DedeUserID") or cookies_by_name.get("DedeUserID")
    try:
        mid_value = int(mid_value) if mid_value not in (None, "") else 0
    except (TypeError, ValueError):
        mid_value = 0

    return {
        "cookie_info": {
            "cookies": normalized_cookies,
            "domains": raw_payload.get("cookie_info", {}).get("domains", [".bilibili.com"]),
        },
        "sso": raw_payload.get("sso", []),
        "token_info": {
            "access_token": token_info.get("access_token", raw_payload.get("access_token", "")),
            "refresh_token": token_info.get("refresh_token", raw_payload.get("refresh_token", "")),
            "expires_in": token_info.get("expires_in", raw_payload.get("expires_in", 0)),
            "mid": mid_value,
        },
        "platform": raw_payload.get("platform", "Android"),
    }


def load_biliup_account_payload(account_path: Path) -> dict:
    """读取并规范化 B 站账号文件，兼容历史扁平格式与 biliup 原生格式。"""

    raw_payload = json.loads(account_path.read_text(encoding="utf-8"))
    return build_biliup_account_payload(raw_payload)


def check_bilibili_account_file(account_file_name: str) -> bool:
    """校验 B 站账号文件是否可用，直接复用 biliup 的 cookie 登录校验。"""

    account_path = resolve_bilibili_account_path(account_file_name)
    if not account_path.exists():
        return False

    try:
        from biliup.plugins.bili_webup import BiliBili, Data

        payload = load_biliup_account_payload(account_path)
        bili_client = BiliBili(Data())
        cookies = {item["name"]: item["value"] for item in payload["cookie_info"]["cookies"]}
        bili_client.login_by_cookies(cookies)
        return True
    except Exception as exc:
        bilibili_logger.error(f"B站账号校验失败，文件={account_path.name}，错误={exc}")
        return False


def post_video_bilibili(
    title: str,
    files: list[str],
    tags,
    account_files: list[str],
    tid: int,
    description: str = "",
    enableTimer: bool = False,
    videos_per_day: int = 1,
    daily_times=None,
    start_days: int = 0,
) -> None:
    """把历史 Web 发布中心的 B 站任务桥接到 `biliup upload`。"""

    if not isinstance(tid, int) or tid <= 0:
        raise ValueError("B站分区ID必须是正整数")

    account_paths = [resolve_bilibili_account_path(file_name) for file_name in account_files]
    video_paths = [resolve_uploaded_video_path(file_name) for file_name in files]
    tags = tags or []
    description_text = description or title

    if enableTimer:
        publish_datetimes = generate_schedule_time_next_day(
            len(video_paths), videos_per_day, daily_times, start_days
        )
    else:
        publish_datetimes = [0 for _ in range(len(video_paths))]

    for index, video_path in enumerate(video_paths):
        if not video_path.exists():
            raise FileNotFoundError(f"B站发布视频文件不存在: {video_path}")

        publish_date = publish_datetimes[index]
        for account_path in account_paths:
            if not account_path.exists():
                raise FileNotFoundError(f"B站账号文件不存在: {account_path}")

            normalized_payload = load_biliup_account_payload(account_path)
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as temp_account_file:
                temp_account_file.write(json.dumps(normalized_payload, ensure_ascii=False))
                temp_account_path = Path(temp_account_file.name)

            try:
                arguments = [
                    "-u",
                    str(temp_account_path),
                    "upload",
                    str(video_path),
                    "--title",
                    title,
                    "--desc",
                    description_text,
                    "--tid",
                    str(tid),
                ]

                if tags:
                    arguments.extend(["--tag", ",".join(tags)])
                if isinstance(publish_date, datetime):
                    arguments.extend(["--dtime", str(int(publish_date.timestamp()))])

                result = run_biliup_command(arguments)
                if result.returncode != 0:
                    raise RuntimeError((result.stderr or result.stdout or "").strip() or "B站发布失败")
            finally:
                temp_account_path.unlink(missing_ok=True)
