import abc
from typing import Any

import structlog

from video_mcp.models.results import VideoResult

logger = structlog.get_logger()

class BaseProvider(abc.ABC):
    def __init__(self, provider_name: str) -> None:
        self.provider_name = provider_name

    @abc.abstractmethod
    async def generate_video(self, request: Any) -> VideoResult:
        """Submits video generation job, polls until complete, and downloads file."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Performs a lightweight endpoint check to verify connection/authentication."""
        pass

    @abc.abstractmethod
    async def get_credit_balance(self) -> float:
        """Returns the remaining credit balance or quota."""
        pass

    def log_call(self, method: str, duration_ms: float, cost_credits: float = 0.0, **kwargs: Any) -> None:
        """Log structured performance metrics for each API call."""
        logger.info(
            "provider_call",
            provider=self.provider_name,
            method=method,
            duration_ms=duration_ms,
            cost_credits=cost_credits,
            **kwargs
        )
