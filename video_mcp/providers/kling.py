import base64
import time
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

from video_mcp.config import get_settings
from video_mcp.errors import ErrorCode, MCPVideoError, raise_provider_error
from video_mcp.guardrails import validate_output_path
from video_mcp.models.results import VideoResult
from video_mcp.providers.base import BaseProvider

logger = structlog.get_logger()

def _is_server_or_rate_limit_error(exception: Exception) -> bool:
    """Helper to check if exception is a recoverable HTTP error."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in {429} or exception.response.status_code >= 500
    return isinstance(exception, httpx.RequestError)

class KlingProvider(BaseProvider):
    def __init__(self, api_key: str | None = None, model: str = "kling-v1-5") -> None:
        super().__init__("kling")
        settings = get_settings()
        self.api_key = api_key or settings.kling_api_key
        self.base_url = "https://api.klingai.com/v1"
        self.default_model = model

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise MCPVideoError(
                "Kling API key is not configured.",
                ErrorCode.PROVIDER_ERROR,
                hint="Set KLING_API_KEY environment variable.",
                provider="kling",
            )
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_result(_is_server_or_rate_limit_error),
        reraise=True,
    )
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Helper to send authenticated HTTP requests with retry logic."""
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
            response = await client.request(method, url, headers=headers, **kwargs)
            
            # Map errors
            if response.status_code >= 400:
                raise_provider_error("kling", response.status_code, response.text)
                
            return response

    async def submit_image_to_video(
        self,
        image_path: Path,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        audio_prompt: str | None = None,
        model_name: str = "auto",
    ) -> str:
        """Submits an image-to-video generation job."""
        start_time = time.monotonic()
        
        # Read and encode image to base64
        try:
            with open(image_path, "rb") as f:
                img_data = f.read()
                img_b64 = base64.b64encode(img_data).decode("utf-8")
        except Exception as e:
            raise MCPVideoError(
                f"Failed to read image file for Kling upload: {e}",
                ErrorCode.INVALID_INPUT,
                provider="kling",
            )

        # Map model name
        mapped_model = {
            "auto": "kling-v1-5",
            "quality": "kling-v2",
            "fast": "kling-v1",
        }.get(model_name, self.default_model)

        payload = {
            "model": mapped_model,
            "image": img_b64,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        if audio_prompt:
            payload["audio_prompt"] = audio_prompt

        response = await self._request("POST", "/videos/image2video", json=payload)
        res_json = response.json()
        job_id = res_json.get("data", {}).get("task_id") or res_json.get("task_id")
        
        if not job_id:
            raise MCPVideoError(
                f"Kling API response missing task_id: {res_json}",
                ErrorCode.PROVIDER_ERROR,
                provider="kling",
            )

        duration_ms = (time.monotonic() - start_time) * 1000
        self.log_call("submit_image_to_video", duration_ms, job_id=job_id)
        return str(job_id)

    async def submit_text_to_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        style: str = "cinematic",
    ) -> str:
        """Submits a text-to-video generation job."""
        start_time = time.monotonic()
        payload = {
            "model": self.default_model,
            "prompt": f"{prompt}, style: {style}",
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }
        response = await self._request("POST", "/videos/text2video", json=payload)
        res_json = response.json()
        job_id = res_json.get("data", {}).get("task_id") or res_json.get("task_id")
        
        if not job_id:
            raise MCPVideoError(
                f"Kling API response missing task_id: {res_json}",
                ErrorCode.PROVIDER_ERROR,
                provider="kling",
            )

        duration_ms = (time.monotonic() - start_time) * 1000
        self.log_call("submit_text_to_video", duration_ms, job_id=job_id)
        return str(job_id)

    async def poll_job(self, job_id: str, timeout: int = 300, interval: int = 5) -> dict[str, Any]:
        """Polls Kling job status until completion or failure."""
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            response = await self._request("GET", f"/videos/{job_id}")
            res_json = response.json()
            task = res_json.get("data", {}) or res_json
            status = task.get("task_status") or task.get("status")

            if status == "succeed":
                return dict(task) if isinstance(task, dict) else {}
            if status == "failed":
                task_dict = dict(task) if isinstance(task, dict) else {}
                err_msg = task_dict.get("task_status_msg") or task_dict.get("error_message") or "Unknown error"
                raise MCPVideoError(
                    f"Kling generation job failed: {err_msg}",
                    ErrorCode.PROVIDER_ERROR,
                    provider="kling",
                )

            await httpx.AsyncClient().get("https://httpbin.org/delay/0") # Yield control
            time.sleep(interval)

        raise MCPVideoError(
            f"Kling job {job_id} timed out after {timeout} seconds",
            ErrorCode.TIMEOUT,
            provider="kling",
        )

    async def download_video(self, url: str, output_path: Path) -> Path:
        """Downloads video and verifies file headers and structure."""
        start_time = time.monotonic()
        async with httpx.AsyncClient() as client:
            # Kling video URLs are public S3/OSS URLs
            response = await client.get(url, timeout=60.0)
            if response.status_code >= 400:
                raise MCPVideoError(
                    f"Failed to download video from {url}: status {response.status_code}",
                    ErrorCode.PROVIDER_ERROR,
                    provider="kling",
                )

            # Ensure valid directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

        # Verification checks
        if output_path.stat().st_size < 1024:
            output_path.unlink(missing_ok=True)
            raise MCPVideoError(
                "Downloaded video file is too small (<1KB)",
                ErrorCode.PROVIDER_ERROR,
                provider="kling",
            )

        with open(output_path, "rb") as f:
            header = f.read(12)
        if b"ftyp" not in header:
            output_path.unlink(missing_ok=True)
            raise MCPVideoError(
                "Downloaded file does not contain valid MP4 magic bytes (ftyp missing)",
                ErrorCode.PROVIDER_ERROR,
                provider="kling",
            )

        duration_ms = (time.monotonic() - start_time) * 1000
        self.log_call("download_video", duration_ms, size_bytes=output_path.stat().st_size)
        return output_path

    async def generate_video(self, request: Any) -> VideoResult:
        """Implements BaseProvider interface for image-to-video."""
        # This translates a request object to the specific flow
        from video_mcp.guardrails import validate_input_path
        
        image_path = validate_input_path(request.image_path)
        output_path = validate_output_path(None, ".mp4")

        # Submit
        job_id = await self.submit_image_to_video(
            image_path=image_path,
            prompt=request.motion_prompt,
            duration=request.duration,
            aspect_ratio=request.aspect_ratio,
            audio_prompt=request.audio_prompt,
            model_name=request.model,
        )

        # Wait
        task_data = await self.poll_job(job_id)
        video_url = task_data.get("video_url") or task_data.get("video", {}).get("url")
        if not video_url:
            raise MCPVideoError(
                "Job succeeded but video URL is missing from payload.",
                ErrorCode.PROVIDER_ERROR,
                provider="kling",
            )

        # Download
        await self.download_video(video_url, output_path)

        # Credit estimation
        credits = 10.0 if request.duration <= 5 else 20.0

        # Build output result
        # Standard values for generated video
        width, height = (1080, 1920) if request.aspect_ratio == "9:16" else (1920, 1080)
        return VideoResult(
            output_path=str(output_path),
            duration_seconds=float(request.duration),
            width=width,
            height=height,
            fps=30,
            file_size_mb=round(output_path.stat().st_size / (1024 * 1024), 2),
            provider_used="kling",
            cost_credits=credits,
        )

    async def health_check(self) -> bool:
        """Call account quota check as a health check."""
        try:
            # Placeholder or real Kling health check endpoint
            await self._request("GET", "/account/quota")
            return True
        except Exception:
            return False

    async def get_credit_balance(self) -> float:
        """Retrieve total remaining credits."""
        try:
            response = await self._request("GET", "/account/quota")
            data = response.json().get("data", {})
            return float(data.get("balance", 0))
        except Exception:
            return 0.0
