from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final


PUBLISH_DRAFTS_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS publish_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""


class PublishDraftError(ValueError):
    """表示发布中心草稿请求不合法或草稿记录不存在。"""

    def __init__(self, message: str, status_code: int = 400) -> None:
        """保存错误文案与接口需要返回的 HTTP 状态码。"""

        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class PublishDraftSummary:
    """草稿列表项，供发布中心渲染草稿清单。"""

    id: int
    name: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class PublishDraftDetail:
    """草稿详情对象，包含完整的发布中心工作区快照。"""

    id: int
    name: str
    workspace: dict[str, object]
    created_at: str
    updated_at: str


def ensure_publish_drafts_table(base_dir: Path) -> None:
    """确保草稿表存在，兼容历史安装尚未执行建表脚本的场景。"""

    db_path = _get_database_path(base_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(PUBLISH_DRAFTS_TABLE_SQL)
        conn.commit()


def save_publish_draft(base_dir: Path, payload: object) -> dict[str, object]:
    """保存或更新发布中心草稿，并返回最新草稿详情。"""

    ensure_publish_drafts_table(base_dir)
    request_payload = _require_payload_dict(payload)
    draft_name = _require_draft_name(request_payload)
    workspace = _require_workspace(request_payload)
    payload_text = json.dumps(workspace, ensure_ascii=False)
    draft_id = _get_optional_draft_id(request_payload)

    with sqlite3.connect(_get_database_path(base_dir)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if draft_id is None:
            cursor.execute(
                """
                INSERT INTO publish_drafts (name, payload)
                VALUES (?, ?)
                """,
                (draft_name, payload_text),
            )
            saved_draft_id = int(cursor.lastrowid)
        else:
            cursor.execute(
                """
                UPDATE publish_drafts
                SET name = ?, payload = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (draft_name, payload_text, draft_id),
            )
            if cursor.rowcount == 0:
                raise PublishDraftError("草稿不存在，无法更新", status_code=404)
            saved_draft_id = draft_id
        conn.commit()

    return get_publish_draft(base_dir, saved_draft_id)


def list_publish_drafts(base_dir: Path) -> list[dict[str, object]]:
    """返回发布中心草稿列表，按最近更新时间倒序展示。"""

    ensure_publish_drafts_table(base_dir)
    with sqlite3.connect(_get_database_path(base_dir)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, created_at, updated_at
            FROM publish_drafts
            ORDER BY datetime(updated_at) DESC, id DESC
            """
        ).fetchall()

    return [asdict(PublishDraftSummary(**dict(row))) for row in rows]


def get_publish_draft(base_dir: Path, draft_id: object) -> dict[str, object]:
    """按草稿 ID 返回完整工作区快照，供前端直接回填页面。"""

    ensure_publish_drafts_table(base_dir)
    normalized_draft_id = _parse_draft_id(draft_id)
    with sqlite3.connect(_get_database_path(base_dir)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, name, payload, created_at, updated_at
            FROM publish_drafts
            WHERE id = ?
            """,
            (normalized_draft_id,),
        ).fetchone()

    if row is None:
        raise PublishDraftError("草稿不存在", status_code=404)

    row_dict = dict(row)
    return asdict(
        PublishDraftDetail(
            id=int(row_dict["id"]),
            name=str(row_dict["name"]),
            workspace=_parse_workspace_json(row_dict["payload"]),
            created_at=str(row_dict["created_at"]),
            updated_at=str(row_dict["updated_at"]),
        )
    )


def delete_publish_draft(base_dir: Path, draft_id: object) -> dict[str, object]:
    """删除指定草稿，避免发布中心继续显示失效记录。"""

    ensure_publish_drafts_table(base_dir)
    normalized_draft_id = _parse_draft_id(draft_id)
    with sqlite3.connect(_get_database_path(base_dir)) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM publish_drafts WHERE id = ?", (normalized_draft_id,))
        if cursor.rowcount == 0:
            raise PublishDraftError("草稿不存在", status_code=404)
        conn.commit()

    return {"id": normalized_draft_id}


def _get_database_path(base_dir: Path) -> Path:
    """统一返回草稿数据库路径，避免多处手写路径拼接。"""

    return Path(base_dir / "db" / "database.db")


def _require_payload_dict(payload: object) -> dict[str, object]:
    """把接口请求约束为对象，避免把无结构数据直接落库。"""

    if not isinstance(payload, dict) or not payload:
        raise PublishDraftError("草稿请求数据不能为空")
    return payload


def _require_draft_name(payload: dict[str, object]) -> str:
    """确保草稿名称存在，便于草稿列表区分不同工作区。"""

    raw_name = payload.get("name")
    draft_name = "" if raw_name is None else str(raw_name).strip()
    if not draft_name:
        raise PublishDraftError("草稿名称不能为空")
    return draft_name


def _require_workspace(payload: dict[str, object]) -> dict[str, object]:
    """要求工作区快照必须是对象，保证后续可直接 JSON 回填。"""

    workspace = payload.get("workspace")
    if not isinstance(workspace, dict) or not workspace:
        raise PublishDraftError("草稿内容不能为空")
    return workspace


def _get_optional_draft_id(payload: dict[str, object]) -> int | None:
    """在保存接口里兼容“新建草稿”和“覆盖现有草稿”两种模式。"""

    raw_draft_id = payload.get("id")
    if raw_draft_id in (None, ""):
        return None
    return _parse_draft_id(raw_draft_id)


def _parse_draft_id(draft_id: object) -> int:
    """把草稿 ID 规范化为正整数，避免查询与删除误入脏值。"""

    try:
        normalized_draft_id = int(draft_id)
    except (TypeError, ValueError) as exc:
        raise PublishDraftError("草稿ID不合法") from exc
    if normalized_draft_id <= 0:
        raise PublishDraftError("草稿ID不合法")
    return normalized_draft_id


def _parse_workspace_json(payload_text: object) -> dict[str, object]:
    """从数据库中的 JSON 文本恢复工作区对象，并校验结构完整性。"""

    try:
        workspace = json.loads(str(payload_text))
    except json.JSONDecodeError as exc:
        raise PublishDraftError("草稿内容已损坏，无法解析", status_code=500) from exc
    if not isinstance(workspace, dict):
        raise PublishDraftError("草稿内容结构不合法", status_code=500)
    return workspace
