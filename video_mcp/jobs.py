import asyncio
import uuid
from typing import Any, Optional

from video_mcp.models.results import JobStatus


class JobManager:
    _instance: Optional["JobManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "JobManager":
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        # Avoid reinitializing if singleton already setup
        if hasattr(self, "_initialized"):
            return
        self._tasks: dict[str, asyncio.Task] = {}
        self._statuses: dict[str, JobStatus] = {}
        self._lock = asyncio.Lock()
        self._initialized = True

    async def submit(self, coro: Any) -> str:
        """Submit a coroutine as a background job."""
        job_id = str(uuid.uuid4())
        
        async with self._lock:
            self._statuses[job_id] = JobStatus(
                job_id=job_id,
                status="pending",
                progress_pct=0.0,
            )

        # Create Task
        task = asyncio.create_task(self._run_job(job_id, coro))
        
        async with self._lock:
            self._tasks[job_id] = task

        return job_id

    async def _run_job(self, job_id: str, coro: Any) -> None:
        try:
            async with self._lock:
                if job_id in self._statuses:
                    self._statuses[job_id].status = "running"
                    self._statuses[job_id].progress_pct = 20.0

            result = await coro
            
            async with self._lock:
                if job_id in self._statuses:
                    out_path = getattr(result, "output_path", None)
                    if out_path:
                        self._statuses[job_id].output_path = str(out_path)
                    self._statuses[job_id].status = "complete"
                    self._statuses[job_id].progress_pct = 100.0
        except asyncio.CancelledError:
            async with self._lock:
                if job_id in self._statuses:
                    self._statuses[job_id].status = "failed"
                    self._statuses[job_id].progress_pct = 100.0
                    self._statuses[job_id].error = "Job was cancelled."
            raise
        except Exception as e:
            async with self._lock:
                if job_id in self._statuses:
                    self._statuses[job_id].status = "failed"
                    self._statuses[job_id].progress_pct = 100.0
                    self._statuses[job_id].error = str(e)

    async def status(self, job_id: str) -> JobStatus:
        """Get the current status of a job."""
        async with self._lock:
            if job_id not in self._statuses:
                return JobStatus(
                    job_id=job_id,
                    status="failed",
                    progress_pct=0.0,
                    error=f"Job {job_id} not found.",
                )
            return self._statuses[job_id]

    async def cancel(self, job_id: str) -> bool:
        """Cancel an active job."""
        async with self._lock:
            task = self._tasks.get(job_id)
            if not task or task.done():
                return False
            task.cancel()
            return True

    async def list_jobs(self, status_filter: str | None = None) -> list[JobStatus]:
        """List all tracked jobs, optionally filtered by status."""
        async with self._lock:
            jobs = list(self._statuses.values())
            if status_filter:
                jobs = [j for j in jobs if j.status == status_filter]
            return jobs

_job_manager: JobManager | None = None

def get_job_manager() -> JobManager:
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
