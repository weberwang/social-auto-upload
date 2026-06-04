from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class TaskEvent:
    """描述 MCP 任务生命周期中的一条事件记录。"""

    event_type: str
    task_id: str
    status: str
    message: str
    timestamp: str
    data: dict[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        task_id: str,
        status: str,
        message: str,
        data: dict[str, object] | None = None,
    ) -> "TaskEvent":
        """构造一条带默认时间戳的任务事件。"""

        return cls(
            event_type=event_type,
            task_id=task_id,
            status=status,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data or {},
        )


@dataclass(slots=True)
class TaskRecord:
    """描述一条 MCP 异步任务记录。"""

    task_id: str
    task_type: str
    platform: str | None
    account_name: str | None
    status: str
    input_payload: dict[str, object]
    result: dict[str, object] | None = None
    error: dict[str, object] | None = None

    @classmethod
    def create(
        cls,
        *,
        task_type: str,
        platform: str | None,
        account_name: str | None,
        input_payload: dict[str, object],
    ) -> "TaskRecord":
        """创建一条默认处于排队状态的任务记录。"""

        return cls(
            task_id=f"task_{uuid4().hex}",
            task_type=task_type,
            platform=platform,
            account_name=account_name,
            status="queued",
            input_payload=input_payload,
        )

