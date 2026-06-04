from __future__ import annotations

import json


def encode_sse(event_name: str, payload: dict[str, object]) -> str:
    """把结构化事件编码为最小可用的 SSE 文本帧。"""

    # 当前阶段只需要单事件、单数据行的标准格式，后续再扩展多行与重连信息。
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
