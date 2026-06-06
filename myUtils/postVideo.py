import asyncio
from pathlib import Path
from typing import Final

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinNote, DouYinVideo
from uploader.ks_uploader.main import KSNote, KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.xiaohongshu_uploader.main import XiaoHongShuNote, XiaoHongShuVideo
from utils.constant import TencentZoneTypes
from utils.files_times import generate_schedule_time_next_day

DEFAULT_VIDEOS_PER_DAY: Final[int] = 1


def _resolve_account_files(account_files: list[str]) -> list[Path]:
    """把账号文件相对路径解析为 cookies 目录下的绝对路径。"""

    return [Path(BASE_DIR / "cookiesFile" / file) for file in account_files]


def _resolve_material_files(files: list[str]) -> list[Path]:
    """把素材相对路径解析为统一素材目录下的绝对路径。"""

    return [Path(BASE_DIR / "videoFile" / file) for file in files]


def _build_publish_datetimes(
    item_count: int,
    enable_timer: bool,
    videos_per_day: int | None,
    daily_times: list[str] | None,
    start_days: int | None,
) -> list[object]:
    """统一生成发布时刻，避免视频/图文链路各自拼时间逻辑。"""

    if not enable_timer:
        return [0 for _ in range(item_count)]

    return generate_schedule_time_next_day(
        item_count,
        videos_per_day or DEFAULT_VIDEOS_PER_DAY,
        daily_times,
        start_days or 0,
    )


def _build_single_publish_datetime(
    enable_timer: bool,
    videos_per_day: int | None,
    daily_times: list[str] | None,
    start_days: int | None,
) -> object:
    """图文一次发布会携带多张图片，因此只需要一个发布时间。"""

    return _build_publish_datetimes(
        1,
        enable_timer,
        videos_per_day,
        daily_times,
        start_days,
    )[0]


def post_video_tencent(
    title,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
    is_draft=False,
):
    """按既有方式把视频号视频请求分发到 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    video_files = _resolve_material_files(files)
    publish_datetimes = _build_publish_datetimes(
        len(video_files),
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for index, file in enumerate(video_files):
        for cookie in cookie_files:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = TencentVideo(title, str(file), tags, publish_datetimes[index], cookie, category, is_draft)
            asyncio.run(app.main(), debug=False)


def post_video_DouYin(
    title,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
    thumbnail_path="",
    productLink="",
    productTitle="",
):
    """按既有方式把抖音视频请求分发到 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    video_files = _resolve_material_files(files)
    publish_datetimes = _build_publish_datetimes(
        len(video_files),
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for index, file in enumerate(video_files):
        for cookie in cookie_files:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = DouYinVideo(title, str(file), tags, publish_datetimes[index], cookie, thumbnail_path, productLink, productTitle)
            asyncio.run(app.douyin_upload_video(), debug=False)


def post_video_ks(
    title,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
):
    """按既有方式把快手视频请求分发到 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    video_files = _resolve_material_files(files)
    publish_datetimes = _build_publish_datetimes(
        len(video_files),
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for index, file in enumerate(video_files):
        for cookie in cookie_files:
            print(f"文件路径{str(file)}")
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = KSVideo(title, str(file), tags, publish_datetimes[index], cookie)
            asyncio.run(app.main(), debug=False)


def post_video_xhs(
    title,
    files,
    tags,
    account_file,
    category=TencentZoneTypes.LIFESTYLE.value,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
):
    """按既有方式把小红书视频请求分发到 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    video_files = _resolve_material_files(files)
    publish_datetimes = _build_publish_datetimes(
        len(video_files),
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for index, file in enumerate(video_files):
        for cookie in cookie_files:
            print(f"视频文件名：{file}")
            print(f"标题：{title}")
            print(f"Hashtag：{tags}")
            app = XiaoHongShuVideo(title, file, tags, publish_datetimes[index], cookie)
            asyncio.run(app.main(), debug=False)


def post_note_DouYin(
    title,
    files,
    note,
    tags,
    account_file,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
):
    """把抖音图文请求分发到图文 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    image_files = [str(path) for path in _resolve_material_files(files)]
    publish_datetime = _build_single_publish_datetime(
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for cookie in cookie_files:
        app = DouYinNote(
            image_paths=image_files,
            title=title,
            note=note,
            tags=tags,
            publish_date=publish_datetime,
            account_file=str(cookie),
        )
        asyncio.run(app.douyin_upload_note(), debug=False)


def post_note_ks(
    title,
    files,
    note,
    tags,
    account_file,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
):
    """把快手图文请求分发到图文 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    image_files = [str(path) for path in _resolve_material_files(files)]
    publish_datetime = _build_single_publish_datetime(
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for cookie in cookie_files:
        app = KSNote(
            image_paths=image_files,
            title=title,
            note=note,
            tags=tags,
            publish_date=publish_datetime,
            account_file=str(cookie),
        )
        asyncio.run(app.main(), debug=False)


def post_note_xhs(
    title,
    files,
    note,
    tags,
    account_file,
    enableTimer=False,
    videos_per_day=DEFAULT_VIDEOS_PER_DAY,
    daily_times=None,
    start_days=0,
):
    """把小红书图文请求分发到图文 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    image_files = [str(path) for path in _resolve_material_files(files)]
    publish_datetime = _build_single_publish_datetime(
        bool(enableTimer),
        videos_per_day,
        daily_times,
        start_days,
    )

    for cookie in cookie_files:
        app = XiaoHongShuNote(
            image_paths=image_files,
            title=title,
            note=note,
            desc=note,
            tags=tags,
            publish_date=publish_datetime,
            account_file=str(cookie),
        )
        asyncio.run(app.main(), debug=False)
