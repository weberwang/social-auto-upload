import asyncio
import time
import unittest

from sau_mcp_server.models.task import TaskRecord
from sau_mcp_server.queue.task_queue import TaskQueue
from sau_mcp_server.repositories.task_repository import InMemoryTaskRepository


class McpTaskQueueTests(unittest.TestCase):
    """验证 MCP 任务队列会把任务从入队推进到成功态。"""

    def test_enqueue_task_saves_record_and_appends_queued_event(self) -> None:
        """入队阶段应只负责保存任务并记录 queued 事件。"""

        repository = InMemoryTaskRepository()
        queue = TaskQueue(repository=repository)
        task = TaskRecord.create(
            task_type="platform.login",
            platform="douyin",
            account_name="creator",
            input_payload={"platform": "douyin"},
        )

        result = queue.enqueue_task(
            task,
            message="平台登录任务已创建",
            data={"tool": "platform_login"},
        )

        self.assertIs(result, task)
        stored = repository.get_task(task.task_id)
        self.assertEqual(stored.status, "queued")
        self.assertEqual(stored.task_type, "platform.login")

        events = repository.list_events(task.task_id)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "task.queued")
        self.assertEqual(events[0].status, "queued")
        self.assertEqual(events[0].message, "平台登录任务已创建")
        self.assertEqual(events[0].data, {"tool": "platform_login"})

    def test_submit_runs_job_and_marks_task_succeeded(self):
        repository = InMemoryTaskRepository()
        queue = TaskQueue(repository=repository)

        async def sample_job():
            return {"ok": True}

        task = TaskRecord.create(
            task_type="platform.check",
            platform="douyin",
            account_name="creator",
            input_payload={},
        )

        queue.enqueue_task(task, message="任务已入队")
        asyncio.run(queue.submit(task, sample_job))

        stored = repository.get_task(task.task_id)
        self.assertEqual(stored.status, "succeeded")
        self.assertEqual(stored.result, {"ok": True})

        events = repository.list_events(task.task_id)
        self.assertEqual(
            [(event.event_type, event.status) for event in events],
            [
                ("task.queued", "queued"),
                ("task.running", "running"),
                ("task.succeeded", "succeeded"),
            ],
        )

    def test_submit_rejects_non_queued_task(self) -> None:
        """执行阶段只能处理已经受理过的任务。"""

        repository = InMemoryTaskRepository()
        queue = TaskQueue(repository=repository)

        async def sample_job():
            return {"ok": True}

        task = TaskRecord.create(
            task_type="platform.check",
            platform="douyin",
            account_name="creator",
            input_payload={},
        )
        task.status = "running"

        with self.assertRaisesRegex(ValueError, "queued"):
            asyncio.run(queue.submit(task, sample_job))

    def test_submit_background_eventually_marks_task_succeeded(self) -> None:
        """后台提交必须真正推进任务状态，而不是永远停在 queued。"""

        repository = InMemoryTaskRepository()
        queue = TaskQueue(repository=repository)

        async def sample_job():
            await asyncio.sleep(0.1)
            return {"ok": True}

        task = TaskRecord.create(
            task_type="platform.login",
            platform="douyin",
            account_name="creator",
            input_payload={},
        )

        queue.enqueue_task(task, message="任务已入队")
        queue.submit_background(task, sample_job)

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            stored_events = repository.list_events(task.task_id)
            if (
                repository.get_task(task.task_id).status in {"succeeded", "failed"}
                and stored_events
                and stored_events[-1].event_type in {"task.succeeded", "task.failed"}
            ):
                break
            time.sleep(0.02)

        stored = repository.get_task(task.task_id)
        self.assertEqual(stored.status, "succeeded")
        self.assertEqual(stored.result, {"ok": True})
        self.assertEqual(
            [(event.event_type, event.status) for event in repository.list_events(task.task_id)],
            [
                ("task.queued", "queued"),
                ("task.running", "running"),
                ("task.succeeded", "succeeded"),
            ],
        )
