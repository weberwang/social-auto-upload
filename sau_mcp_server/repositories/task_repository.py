from __future__ import annotations

from typing import Protocol

from sau_mcp_server.models.task import TaskEvent, TaskRecord


class TaskRepository(Protocol):
    """定义任务仓储需要支持的最小读写接口。"""

    def save_task(self, task: TaskRecord) -> None:
        """保存或更新一条任务记录。"""

    def get_task(self, task_id: str) -> TaskRecord:
        """按任务 ID 读取任务记录。"""

    def append_event(self, event: TaskEvent) -> None:
        """追加一条任务事件。"""

    def list_events(self, task_id: str) -> list[TaskEvent]:
        """读取某个任务的事件历史。"""


class InMemoryTaskRepository:
    """以内存字典保存任务与事件，适合当前阶段快速接入。"""

    def __init__(self) -> None:
        """初始化任务与事件缓存。"""

        self._tasks: dict[str, TaskRecord] = {}
        self._events: dict[str, list[TaskEvent]] = {}

    def save_task(self, task: TaskRecord) -> None:
        """保存或覆盖任务记录，并保证事件容器已初始化。"""

        self._tasks[task.task_id] = task
        self._events.setdefault(task.task_id, [])

    def get_task(self, task_id: str) -> TaskRecord:
        """读取指定任务；不存在时直接抛出键错误，便于上层定位问题。"""

        return self._tasks[task_id]

    def append_event(self, event: TaskEvent) -> None:
        """把任务事件按任务 ID 追加到历史列表。"""

        self._events.setdefault(event.task_id, []).append(event)

    def list_events(self, task_id: str) -> list[TaskEvent]:
        """返回某个任务的事件副本，避免外部直接污染仓储内部状态。"""

        return list(self._events.get(task_id, []))

