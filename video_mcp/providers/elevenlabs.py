import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_result, stop_after_attempt, wait_exponential

from video_mcp.config import get_settings
from video_mcp.errors import ErrorCode, MCPVideoError, raise_provider_error
from video_mcp.guardrails import validate_output_path
from video_mcp.models.results import AudioResult

logger = structlog.get_logger()

def _is_rate_limit(exception: Exception) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code == 429
    return False

def get_audio_duration(path: Path) -> float:
    """Gets audio duration using ffprobe or falls back to size-based estimation."""
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception:
        # Fallback: MP3 typical bitrate (128kbps) is 16,000 bytes per second
        size = path.stat().st_size
        return max(0.5, float(size) / 16000.0)

class ElevenLabsProvider:
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    def _get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise MCPVideoError(
                "ElevenLabs API key is not configured.",
                ErrorCode.PROVIDER_ERROR,
                hint="Set ELEVENLABS_API_KEY environment variable.",
                provider="elevenlabs",
            )
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_result(_is_rate_limit),
        reraise=True,
    )
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
            response = await client.request(method, url, headers=headers, **kwargs)
            if response.status_code >= 400:
                raise_provider_error("elevenlabs", response.status_code, response.text)
            return response

    async def generate_voiceover(
        self,
        script: str,
        voice_id: str = "adam",
        speed: float = 0.95,
        output_path: str | None = None,
    ) -> AudioResult:
        """Synthesizes text script to voiceover audio file using ElevenLabs."""
        start_time = time.monotonic()
        
        # Validate and prepare output destination
        final_output = validate_output_path(output_path, ".mp3")

        payload = {
            "text": script,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "speed": speed,
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }

        # Make request directly streaming content
        headers = self._get_headers()
        url = f"{self.base_url.rstrip('/')}/text-to-speech/{voice_id}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code >= 400:
                        body_text = await response.aread()
                        raise_provider_error("elevenlabs", response.status_code, body_text.decode("utf-8"))
                    
                    with open(final_output, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
        except Exception as e:
            if isinstance(e, MCPVideoError):
                raise e
            raise MCPVideoError(
                f"ElevenLabs connection failure: {e}",
                ErrorCode.PROVIDER_ERROR,
                provider="elevenlabs",
            )

        duration = get_audio_duration(final_output)
        char_count = len(script)
        
        # ElevenLabs charges 1 credit per character
        cost = float(char_count)

        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info(
            "provider_call",
            provider="elevenlabs",
            method="generate_voiceover",
            duration_ms=duration_ms,
            cost_credits=cost,
            char_count=char_count,
        )

        return AudioResult(
            output_path=str(final_output),
            duration_seconds=duration,
            voice_id=voice_id,
            character_count=char_count,
            cost_credits=cost,
        )

    async def list_voices(self) -> list[dict[str, Any]]:
        """Lists available voice identifiers."""
        response = await self._request("GET", "/voices")
        data = response.json()
        voices = []
        for v in data.get("voices", []):
            voices.append({
                "id": v.get("voice_id"),
                "name": v.get("name"),
                "category": v.get("category"),
            })
        return voices

    async def get_remaining_chars(self) -> int:
        """Fetch remaining character balance."""
        try:
            response = await self._request("GET", "/user")
            data = response.json()
            remaining = int(data.get("subscription", {}).get("character_count", 0))
            limit = int(data.get("subscription", {}).get("character_limit", 0))
            return int(max(0, limit - remaining))
        except Exception:
            return 0
