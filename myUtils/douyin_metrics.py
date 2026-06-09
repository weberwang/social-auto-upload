from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Final

from patchright.async_api import async_playwright

from conf import LOCAL_CHROME_HEADLESS
from uploader.douyin_uploader.main import DOUYIN_HOME_URL, cookie_auth as douyin_cookie_auth
from utils.base_social_media import set_init_script

METRIC_LABEL_GROUPS: Final[dict[str, tuple[str, ...]]] = {
    "follower_count": ("粉丝数", "粉丝"),
    "like_count": ("获赞数", "获赞", "点赞数", "点赞"),
    "following_count": ("关注数", "关注"),
    "work_count": ("作品数", "作品"),
    "total_view_count": ("总播放量", "累计播放", "播放量", "播放"),
}
METRIC_VALUE_PATTERN: Final[str] = r"[0-9]+(?:\.[0-9]+)?(?:[万亿wW])?"


class DouyinMetricsError(RuntimeError):
    """表示抖音运营数据抓取流程遇到了可预期的账号或页面异常。"""


@dataclass(frozen=True, slots=True)
class DouyinMetricsTextSnapshot:
    """承载从抖音创作者中心页面文本中解析出的统一指标。"""

    follower_count: int | None
    like_count: int | None
    following_count: int | None
    work_count: int | None
    total_view_count: int | None
    raw_metrics: dict[str, int | None]


@dataclass(frozen=True, slots=True)
class DouyinAccountMetricsSnapshot:
    """表示单个抖音账号当前抓取到的运营概览。"""

    account_name: str
    account_file: str
    current_url: str
    captured_at: str
    follower_count: int | None
    like_count: int | None
    following_count: int | None
    work_count: int | None
    total_view_count: int | None
    raw_metrics: dict[str, int | None]

    def to_dict(self) -> dict[str, object]:
        """把概览结果转成接口层可直接返回的字典结构。"""

        return asdict(self)


def parse_douyin_metric_value(raw_value: str) -> int | None:
    """把抖音页面上的中文单位数值转换成整数，空占位返回 `None`。"""

    normalized_value = str(raw_value or "").strip().replace(",", "")
    if normalized_value in {"", "--", "-"}:
        return None

    unit_multiplier = 1
    if normalized_value.endswith(("万", "w", "W")):
        unit_multiplier = 10_000
        normalized_value = normalized_value[:-1]
    elif normalized_value.endswith("亿"):
        unit_multiplier = 100_000_000
        normalized_value = normalized_value[:-1]

    return int(float(normalized_value) * unit_multiplier)


def _normalize_page_text(page_text: str) -> str:
    """统一压缩空白字符，降低页面换行对指标正则匹配的影响。"""

    return re.sub(r"\s+", " ", page_text or "").strip()


def _extract_metric_value(page_text: str, labels: tuple[str, ...]) -> tuple[str | None, int | None]:
    """按候选标签顺序提取单项指标，兼容“标签在前”与“数值在前”两种文案布局。"""

    normalized_text = _normalize_page_text(page_text)
    for label in labels:
        direct_pattern = re.compile(rf"{re.escape(label)}\s*[:：]?\s*({METRIC_VALUE_PATTERN})")
        direct_match = direct_pattern.search(normalized_text)
        if direct_match:
            return label, parse_douyin_metric_value(direct_match.group(1))

        reverse_pattern = re.compile(rf"({METRIC_VALUE_PATTERN})\s*{re.escape(label)}")
        reverse_match = reverse_pattern.search(normalized_text)
        if reverse_match:
            return label, parse_douyin_metric_value(reverse_match.group(1))

    return None, None


def extract_douyin_metrics_from_text(page_text: str) -> DouyinMetricsTextSnapshot:
    """从抖音创作者中心页面文本中提取统一账号指标。"""

    extracted_values: dict[str, int | None] = {}
    raw_metrics: dict[str, int | None] = {}

    for field_name, labels in METRIC_LABEL_GROUPS.items():
        matched_label, metric_value = _extract_metric_value(page_text, labels)
        extracted_values[field_name] = metric_value
        if matched_label:
            raw_metrics[matched_label] = metric_value

    return DouyinMetricsTextSnapshot(
        follower_count=extracted_values["follower_count"],
        like_count=extracted_values["like_count"],
        following_count=extracted_values["following_count"],
        work_count=extracted_values["work_count"],
        total_view_count=extracted_values["total_view_count"],
        raw_metrics=raw_metrics,
    )


async def fetch_douyin_account_metrics(account_file: Path, account_name: str) -> DouyinAccountMetricsSnapshot:
    """复用现有抖音登录态打开创作者首页，并抓取当前账号概览数据。"""

    if not account_file.exists():
        raise DouyinMetricsError(f"抖音账号 Cookie 文件不存在: {account_file}")
    if not await douyin_cookie_auth(account_file):
        raise DouyinMetricsError(f"抖音账号登录态已失效，请重新登录: {account_name}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS, channel="chrome")
        try:
            context = await browser.new_context(storage_state=account_file)
            context = await set_init_script(context)
            page = await context.new_page()
            await page.goto(DOUYIN_HOME_URL, wait_until="domcontentloaded", timeout=15000)
            await page.locator("body").wait_for(state="visible", timeout=15000)
            body_text = await page.locator("body").inner_text()
            metrics_snapshot = extract_douyin_metrics_from_text(body_text)
            if not metrics_snapshot.raw_metrics:
                raise DouyinMetricsError("未在抖音创作者中心页面识别到可用运营指标")

            return DouyinAccountMetricsSnapshot(
                account_name=account_name,
                account_file=account_file.name,
                current_url=page.url,
                captured_at=datetime.now().isoformat(timespec="seconds"),
                follower_count=metrics_snapshot.follower_count,
                like_count=metrics_snapshot.like_count,
                following_count=metrics_snapshot.following_count,
                work_count=metrics_snapshot.work_count,
                total_view_count=metrics_snapshot.total_view_count,
                raw_metrics=metrics_snapshot.raw_metrics,
            )
        finally:
            await browser.close()
