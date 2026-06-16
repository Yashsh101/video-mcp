import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from video_mcp.errors import MCPVideoError, ErrorCode
from video_mcp.models.schemas import SceneRequest
from video_mcp.config import get_settings
from video_mcp.tools.generate import (
    generate_video_from_image,
    batch_generate_scenes,
    generate_voiceover,
)

@pytest.mark.asyncio
async def test_generate_video_from_image_success(sample_image, mock_kling_provider):
    """Verify image to video returns VideoResult containing valid output."""
    res = await generate_video_from_image(
        image_path=str(sample_image),
        motion_prompt="pan right, Pixar style",
        duration=5,
        provider="kling",
    )
    assert res.output_path.endswith("mock_output.mp4")
    assert res.duration_seconds == 5.0

@pytest.mark.asyncio
async def test_generate_video_from_image_missing_image():
    """Verify input validation fails if reference image does not exist."""
    settings = get_settings()
    with pytest.raises(MCPVideoError) as exc_info:
        await generate_video_from_image(
            image_path=str(settings.work_dir / "nonexistent_image.png"),
            motion_prompt="pan right",
            provider="kling",
        )
    assert exc_info.value.code == ErrorCode.FILE_NOT_FOUND

@pytest.mark.asyncio
async def test_batch_generate_scenes(sample_image, mock_kling_provider):
    """Verify batch processing calls provider and compiles results."""
    scenes = [
        SceneRequest(scene_number=1, image_path=str(sample_image), motion_prompt="pan left"),
        SceneRequest(scene_number=2, image_path=str(sample_image), motion_prompt="pan right"),
    ]
    batch_res = await batch_generate_scenes(scenes=scenes, provider="kling")
    assert len(batch_res.results) == 2
    assert mock_kling_provider.generate_video.call_count == 2
    assert batch_res.total_duration_seconds == 10.0

@pytest.mark.asyncio
async def test_batch_generate_scenes_partial_failure(sample_image, mock_kling_provider):
    """Verify batch processing tolerates individual failures and records scene indices."""
    from video_mcp.models.results import VideoResult
    # Setup kling mock to throw error on second call
    mock_kling_provider.generate_video = AsyncMock(
        side_effect=[
            VideoResult(
                output_path="mock_output.mp4",
                duration_seconds=5.0,
                width=1080,
                height=1920,
                fps=30,
                file_size_mb=1.2,
                provider_used="kling",
                cost_credits=10.0,
            ),  # first call succeeds
            Exception("Kling API request timeout"),  # second call fails
        ]
    )
    scenes = [
        SceneRequest(scene_number=1, image_path=str(sample_image), motion_prompt="scene one"),
        SceneRequest(scene_number=2, image_path=str(sample_image), motion_prompt="scene two"),
    ]
    batch_res = await batch_generate_scenes(scenes=scenes, provider="kling")
    assert len(batch_res.results) == 1
    assert batch_res.failed_scenes == [2]

@pytest.mark.asyncio
async def test_generate_voiceover(mock_elevenlabs_provider):
    """Verify voiceover helper maps to ElevenLabs TTS results."""
    res = await generate_voiceover(
        script="Bob was starting an internship.",
        voice_id="adam",
    )
    assert res.output_path.endswith("mock_voiceover.mp3")
    assert res.character_count == 31
