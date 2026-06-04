from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any

from sau_mcp_server.models.task import TaskEvent, TaskRecord
from sau_mcp_server.repositories.task_repository import TaskRepository


class TaskQueue:
    """顺序执行 MCP 任务，并把状态与结果写回仓储。"""

    def __init__(self, repository: TaskRepository) -> None:
        """保存仓储引用，后续所有任务状态都通过它回写。"""

        self.repository = repository
        self._lock: asyncio.Lock | None = None
        self._execution_lock = threading.Lock()

    def size(self) -> int:
        """返回当前已保存任务数量，供健康检查等轻量场景使用。"""

        tasks = getattr(self.repository, "_tasks", {})
        return len(tasks)

    def enqueue_task(
        self,
        task: TaskRecord,
        *,
        message: str,
        data: dict[str, object] | None = None,
    ) -> TaskRecord:
        """只负责保存新任务并追加 queued 事件，不承担执行职责。"""

        self.repository.save_task(task)
        self.repository.append_event(
            TaskEvent.create(
                event_type="task.queued",
                task_id=task.task_id,
                status="queued",
                message=message,
                data=data,
            )
        )
        return task

    async def _run_task(self, task: TaskRecord, job_factory: Callable[[], Awaitable[Any]]) -> TaskRecord:
        """执行任务生命周期：running -> succeeded/failed，并写回事件历史。"""

        if task.status != "queued":
            raise ValueError(f"Task must be queued before submit, got {task.status!r}")

        task.status = "running"
        self.repository.save_task(task)
        self.repository.append_event(
            TaskEvent.create(
                event_type="task.running",
                task_id=task.task_id,
                status="running",
                message="任务开始执行",
            )
        )

        try:
            result = await job_factory()
        except Exception as exc:  # pragma: no cover - 失败分支由后续任务覆盖
            # 失败态先保留结构化错误，方便后续 SSE 和 HTTP 层直接透传。
            task.status = "failed"
            task.error = {
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
            self.repository.save_task(task)
            self.repository.append_event(
                TaskEvent.create(
                    event_type="task.failed",
                    task_id=task.task_id,
                    status="failed",
                    message="任务执行失败",
                    data=task.error,
                )
            )
            raise

        task.status = "succeeded"
        task.result = result if isinstance(result, dict) else {"value": result}
        self.repository.save_task(task)
        self.repository.append_event(
            TaskEvent.create(
                event_type="task.succeeded",
                task_id=task.task_id,
                status="succeeded",
                message="任务执行成功",
                data=task.result,
            )
        )
        return task

    async def submit(self, task: TaskRecord, job_factory: Callable[[], Awaitable[Any]]) -> TaskRecord:
        """提交一个任务并顺序执行；当前版本不引入复杂并发。"""

        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            return await self._run_task(task, job_factory)

    def submit_background(self, task: TaskRecord, job_factory: Callable[[], Awaitable[Any]]) -> TaskRecord:
        """把任务放到后台线程执行，HTTP 层可以立即返回受理结果。"""

        if task.status != "queued":
            raise ValueError(f"Task must be queued before submit, got {task.status!r}")

        def _worker() -> None:
            """在独立线程里串行执行任务，避免阻塞 HTTP 请求线程。"""

            with self._execution_lock:
                try:
                    asyncio.run(self._run_task(task, job_factory))
                except Exception:
                    # 失败状态已经写回仓储，这里只需要让后台线程安静退出。
                    pass

        threading.Thread(target=_worker, daemon=True).start()
        return task
