import asyncio
from pathlib import Path
from typing import Final

from conf import BASE_DIR
from uploader.douyin_uploader.main import DouYinNote, DouYinVideo
from uploader.ks_uploader.main import KSNote, KSVideo
from uploader.tencent_uploader.main import TencentVideo
from uploader.wechatmp_uploader.main import WeChatMpArticle
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
    thumbnail_path="",
    thumbnail_landscape_path="",
    thumbnail_portrait_path="",
    short_title="",
    collection_name="",
    declare_original=False,
    original_type="",
    content_declaration="",
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
            # 视频号平台专属字段统一在桥接层显式透传，避免发布中心和 CLI 长期维护两套不一致能力面。
            app = TencentVideo(
                title=title,
                file_path=str(file),
                tags=tags,
                publish_date=publish_datetimes[index],
                account_file=cookie,
                category=category,
                is_draft=is_draft,
                thumbnail_path=thumbnail_path or None,
                thumbnail_landscape_path=thumbnail_landscape_path or None,
                thumbnail_portrait_path=thumbnail_portrait_path or None,
                short_title=short_title or None,
            )
            app.collection_name = collection_name
            app.declare_original = declare_original
            app.original_type = original_type
            app.content_declaration = content_declaration
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
    location="",
    self_declaration="内容为个人观点或见解",
    sync_to_toutiao_xigua=True,
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
            # 抖音专属字段统一走关键字参数，避免位置参数和 uploader 构造函数继续隐式耦合。
            app = DouYinVideo(
                title=title,
                file_path=str(file),
                tags=tags,
                publish_date=publish_datetimes[index],
                account_file=cookie,
                thumbnail_portrait_path=thumbnail_path or None,
                productLink=productLink,
                productTitle=productTitle,
                desc=title,
                location=location,
                self_declaration=self_declaration,
                sync_to_toutiao_xigua=sync_to_toutiao_xigua,
            )
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
    thumbnail_path="",
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
            # 快手视频专属封面直接复用主线 uploader 的 thumbnail_path，避免历史 Web 桥接继续丢字段。
            app = KSVideo(
                title=title,
                file_path=str(file),
                tags=tags,
                publish_date=publish_datetimes[index],
                account_file=cookie,
                thumbnail_path=thumbnail_path or None,
            )
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
    thumbnail_path="",
    location="",
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
            # 小红书专属封面和位置都复用主线 uploader 现有能力，桥接层只负责把字段显式透传下去。
            app = XiaoHongShuVideo(
                title=title,
                file_path=file,
                tags=tags,
                publish_date=publish_datetimes[index],
                account_file=cookie,
                thumbnail_path=thumbnail_path or None,
                location=location,
            )
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
    location="",
    self_declaration="内容为个人观点或见解",
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
            location=location,
            self_declaration=self_declaration,
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
    location="",
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
            location=location,
        )
        asyncio.run(app.main(), debug=False)


def post_note_wechatmp(
    title,
    files,
    note,
    tags,
    account_file,
):
    """把微信公众号图文请求分发到公众号 uploader。"""

    cookie_files = _resolve_account_files(account_file)
    image_files = [str(path) for path in _resolve_material_files(files)]

    for cookie in cookie_files:
        app = WeChatMpArticle(
            image_paths=image_files,
            title=title,
            note=note,
            tags=tags,
            account_file=str(cookie),
        )
        asyncio.run(app.main(), debug=False)
