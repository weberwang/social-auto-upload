from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from myUtils.bilibili_web_bridge import post_video_bilibili
from myUtils.postVideo import (
    post_note_DouYin,
    post_note_ks,
    post_note_xhs,
    post_video_DouYin,
    post_video_ks,
    post_video_tencent,
    post_video_xhs,
)

VIDEO_CONTENT_TYPE: Final = "video"
IMAGE_TEXT_CONTENT_TYPE: Final = "image_text"
SUPPORTED_IMAGE_TEXT_PLATFORM_TYPES: Final[frozenset[int]] = frozenset({1, 3, 4})
PLATFORM_NAME_BY_TYPE: Final[dict[int, str]] = {
    1: "小红书",
    2: "视频号",
    3: "抖音",
    4: "快手",
    5: "B站",
}

ContentType = Literal["video", "image_text"]


class PublishRequestError(ValueError):
    """表示历史 Web 发布接口的请求数据不合法。"""


@dataclass(frozen=True, slots=True)
class WebPublishRequest:
    """统一承载发布中心提交到历史 Web 接口的请求字段。"""

    platform_type: int
    content_type: ContentType
    file_list: tuple[str, ...]
    account_list: tuple[str, ...]
    title: str
    tags: tuple[str, ...]
    description: str
    note_content: str
    tid: int | None
    category: int | None
    enable_timer: bool | int
    videos_per_day: int | None
    daily_times: tuple[str, ...]
    start_days: int | None
    product_link: str
    product_title: str
    thumbnail_path: str
    is_draft: bool
    platform_fields: dict[str, object]


def _require_payload_object(payload: object) -> dict[str, object]:
    """在 Flask 边界处把 JSON 请求约束为对象。"""

    if not isinstance(payload, dict) or not payload:
        raise PublishRequestError("请求数据不能为空")
    return payload


def _require_non_empty_string_list(payload: dict[str, object], key: str, empty_message: str) -> tuple[str, ...]:
    """把列表字段标准化为字符串元组，避免后续分发再处理脏值。"""

    raw_value = payload.get(key, [])
    if not isinstance(raw_value, list):
        raise PublishRequestError(empty_message)

    normalized_values = tuple(str(item).strip() for item in raw_value if str(item).strip())
    if not normalized_values:
        raise PublishRequestError(empty_message)
    return normalized_values


def _get_string(payload: dict[str, object], key: str, default: str = "") -> str:
    """把文本字段统一转成去空白字符串。"""

    raw_value = payload.get(key, default)
    if raw_value is None:
        return default
    return str(raw_value).strip()


def _get_int(payload: dict[str, object], key: str) -> int | None:
    """按需把数字字段解析为整数，空值返回 None。"""

    raw_value = payload.get(key)
    if raw_value is None or str(raw_value).strip() == "":
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError) as exc:
        raise PublishRequestError(f"{key} 必须是整数") from exc


def _get_content_type(payload: dict[str, object]) -> ContentType:
    """兼容老请求默认走视频，新请求显式声明图文。"""

    content_type = _get_string(payload, "contentType", VIDEO_CONTENT_TYPE) or VIDEO_CONTENT_TYPE
    if content_type not in {VIDEO_CONTENT_TYPE, IMAGE_TEXT_CONTENT_TYPE}:
        raise PublishRequestError(f"不支持的内容类型: {content_type}")
    return content_type


def _get_string_tuple(payload: dict[str, object], key: str) -> tuple[str, ...]:
    """把可选字符串列表标准化为元组，空值直接返回空集合语义。"""

    raw_value = payload.get(key, [])
    if not isinstance(raw_value, list):
        return tuple()
    return tuple(str(item).strip() for item in raw_value if str(item).strip())


def _get_object(payload: dict[str, object], key: str) -> dict[str, object]:
    """读取可选对象字段；新旧请求结构并存时统一走这里兜底。"""

    raw_value = payload.get(key)
    return raw_value if isinstance(raw_value, dict) else {}


def _pick_int(*values: object) -> int | None:
    """按优先级挑选整数值，避免新旧字段并存时重复写转换逻辑。"""

    for raw_value in values:
        if raw_value is None or str(raw_value).strip() == "":
            continue
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            continue
    return None


def parse_web_publish_request(payload: object) -> WebPublishRequest:
    """把历史 Web 发布请求解析为强类型对象。"""

    request_payload = _require_payload_object(payload)
    base_fields = _get_object(request_payload, "baseFields")
    platform_fields = _get_object(request_payload, "platformFields")
    douyin_platform_fields = platform_fields.get("douyin")
    bilibili_platform_fields = platform_fields.get("bilibili")
    tencent_platform_fields = platform_fields.get("tencent")
    platform_type = _get_int(request_payload, "type")
    if platform_type is None:
        raise PublishRequestError("平台类型不能为空")
    if platform_type not in PLATFORM_NAME_BY_TYPE:
        raise PublishRequestError(f"不支持的平台类型: {platform_type}")

    field_source = base_fields if base_fields else request_payload
    title = _get_string(field_source, "title")
    if not title:
        raise PublishRequestError("标题不能为空")

    content_type = _get_content_type(request_payload)
    description = _get_string(field_source, "description")
    note_content = _get_string(field_source, "noteContent")
    if content_type == IMAGE_TEXT_CONTENT_TYPE and not note_content:
        # 兼容旧字段，避免前端切换过程中短时间内仍传 description。
        note_content = description

    publish_request = WebPublishRequest(
        platform_type=platform_type,
        content_type=content_type,
        file_list=_require_non_empty_string_list(request_payload, "fileList", "文件列表不能为空"),
        account_list=_require_non_empty_string_list(request_payload, "accountList", "账号列表不能为空"),
        title=title,
        tags=_get_string_tuple(field_source, "tags"),
        description=description,
        note_content=note_content,
        tid=_pick_int(
            bilibili_platform_fields.get("tid") if isinstance(bilibili_platform_fields, dict) else None,
            request_payload.get("tid"),
        ),
        category=_get_int(request_payload, "category"),
        enable_timer=field_source.get("enableTimer", request_payload.get("enableTimer", False)),
        videos_per_day=_pick_int(field_source.get("videosPerDay"), request_payload.get("videosPerDay")),
        daily_times=tuple(str(item).strip() for item in field_source.get("dailyTimes", []) if str(item).strip())
        if isinstance(field_source.get("dailyTimes", []), list)
        else tuple(),
        start_days=_pick_int(field_source.get("startDays"), request_payload.get("startDays")),
        product_link=_get_string(
            douyin_platform_fields if isinstance(douyin_platform_fields, dict) else request_payload,
            "productLink",
        ),
        product_title=_get_string(
            douyin_platform_fields if isinstance(douyin_platform_fields, dict) else request_payload,
            "productTitle",
        ),
        thumbnail_path=_get_string(request_payload, "thumbnail"),
        is_draft=bool(
            tencent_platform_fields.get("isDraft")
            if isinstance(tencent_platform_fields, dict) and "isDraft" in tencent_platform_fields
            else request_payload.get("isDraft", False)
        ),
        platform_fields=platform_fields,
    )
    validate_web_publish_request(publish_request)
    return publish_request


def validate_web_publish_request(publish_request: WebPublishRequest) -> None:
    """校验请求与平台能力是否匹配。"""

    if publish_request.content_type == IMAGE_TEXT_CONTENT_TYPE:
        if publish_request.platform_type not in SUPPORTED_IMAGE_TEXT_PLATFORM_TYPES:
            platform_name = PLATFORM_NAME_BY_TYPE[publish_request.platform_type]
            raise PublishRequestError(f"{platform_name} 当前不支持图文发布")
        return

    if publish_request.platform_type == 5 and publish_request.tid is None:
        raise PublishRequestError("B站分区ID不能为空")


def dispatch_web_publish_request(publish_request: WebPublishRequest) -> None:
    """按内容类型和平台能力把请求分发到现有 uploader。"""

    if publish_request.content_type == IMAGE_TEXT_CONTENT_TYPE:
        dispatch_image_text_request(publish_request)
        return
    dispatch_video_request(publish_request)


def dispatch_video_request(publish_request: WebPublishRequest) -> None:
    """沿用既有视频发布链路。"""

    match publish_request.platform_type:
        case 1:
            post_video_xhs(
                publish_request.title,
                list(publish_request.file_list),
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.category,
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
            )
        case 2:
            post_video_tencent(
                publish_request.title,
                list(publish_request.file_list),
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.category,
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
                publish_request.is_draft,
            )
        case 3:
            post_video_DouYin(
                publish_request.title,
                list(publish_request.file_list),
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.category,
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
                publish_request.thumbnail_path,
                publish_request.product_link,
                publish_request.product_title,
            )
        case 4:
            post_video_ks(
                publish_request.title,
                list(publish_request.file_list),
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.category,
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
            )
        case 5:
            post_video_bilibili(
                publish_request.title,
                list(publish_request.file_list),
                list(publish_request.tags),
                list(publish_request.account_list),
                int(publish_request.tid or 0),
                description=publish_request.description,
                enableTimer=publish_request.enable_timer,
                videos_per_day=publish_request.videos_per_day,
                daily_times=list(publish_request.daily_times),
                start_days=publish_request.start_days,
            )


def dispatch_image_text_request(publish_request: WebPublishRequest) -> None:
    """把图文请求分发到已存在的图文 uploader。"""

    match publish_request.platform_type:
        case 1:
            post_note_xhs(
                publish_request.title,
                list(publish_request.file_list),
                publish_request.note_content,
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
            )
        case 3:
            post_note_DouYin(
                publish_request.title,
                list(publish_request.file_list),
                publish_request.note_content,
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
            )
        case 4:
            post_note_ks(
                publish_request.title,
                list(publish_request.file_list),
                publish_request.note_content,
                list(publish_request.tags),
                list(publish_request.account_list),
                publish_request.enable_timer,
                publish_request.videos_per_day,
                list(publish_request.daily_times),
                publish_request.start_days,
            )
        case _:
            platform_name = PLATFORM_NAME_BY_TYPE[publish_request.platform_type]
            raise PublishRequestError(f"{platform_name} 当前不支持图文发布")
