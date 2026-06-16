import pytest
from pathlib import Path
from unittest.mock import MagicMock

from video_mcp.models.results import AudioResult, VideoResult
from video_mcp.tools.generate import generate_video_from_image, generate_voiceover

@pytest.mark.asyncio
async def test_voiceover_caching(monkeypatch, settings_override):
    """Verify that generate_voiceover saves results in the cache and hits it on subsequent runs."""
    settings = settings_override
    call_count = 0

    async def mock_generate_voiceover(script, voice_id="adam", speed=0.95, output_path=None):
        nonlocal call_count
        call_count += 1
        out_path = Path(output_path) if output_path else settings.work_dir / "mock_voiceover.mp3"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"mock audio data")
        return AudioResult(
            output_path=str(out_path),
            duration_seconds=3.5,
            voice_id=voice_id,
            character_count=len(script),
            cost_credits=float(len(script)),
        )

    mock_provider = MagicMock()
    mock_provider.generate_voiceover = mock_generate_voiceover
    monkeypatch.setattr("video_mcp.tools.generate.ElevenLabsProvider", lambda *a, **kw: mock_provider)

    script = "Hello cache test"
    voice_id = "adam"
    output1 = settings.work_dir / "vo1.mp3"

    # Call 1 (Cache Miss)
    res1 = await generate_voiceover(script=script, voice_id=voice_id, output_path=str(output1))
    assert call_count == 1
    assert Path(res1.output_path).exists()
    assert Path(res1.output_path).read_bytes() == b"mock audio data"

    # Cache files exist
    cache_dir = settings.work_dir / ".mcp_cache"
    assert cache_dir.exists()
    assert len(list(cache_dir.glob("vo_*.mp3"))) == 1

    # Clear target file from output directory
    output1.unlink()

    # Call 2 (Cache Hit)
    output2 = settings.work_dir / "vo2.mp3"
    res2 = await generate_voiceover(script=script, voice_id=voice_id, output_path=str(output2))
    assert call_count == 1  # call_count has not increased
    assert Path(res2.output_path).exists()
    assert Path(res2.output_path).read_bytes() == b"mock audio data"

@pytest.mark.asyncio
async def test_video_caching(monkeypatch, sample_image, settings_override):
    """Verify that generate_video_from_image saves results in the cache and hits it on subsequent runs."""
    settings = settings_override
    call_count = 0

    async def mock_generate_video(req):
        nonlocal call_count
        call_count += 1
        out = settings.work_dir / "mock_output.mp4"
        out.write_bytes(b"mock video data")
        return VideoResult(
            output_path=str(out),
            duration_seconds=req.duration,
            width=1080,
            height=1920,
            fps=30,
            file_size_mb=1.2,
            provider_used=req.provider,
            cost_credits=10.0,
        )

    mock_provider = MagicMock()
    mock_provider.generate_video = mock_generate_video
    monkeypatch.setattr("video_mcp.tools.generate.KlingProvider", lambda *a, **kw: mock_provider)

    motion_prompt = "zoom in pixar"

    # Call 1 (Cache Miss)
    res1 = await generate_video_from_image(
        image_path=str(sample_image),
        motion_prompt=motion_prompt,
        duration=5,
        provider="kling",
    )
    assert call_count == 1
    assert Path(res1.output_path).exists()
    assert Path(res1.output_path).read_bytes() == b"mock video data"

    # Verify cache files exist
    cache_dir = settings.work_dir / ".mcp_cache"
    cached_mp4s = list(cache_dir.glob("video_*.mp4"))
    cached_jsons = list(cache_dir.glob("video_*.json"))
    assert len(cached_mp4s) == 1
    assert len(cached_jsons) == 1

    # Call 2 (Cache Hit)
    res2 = await generate_video_from_image(
        image_path=str(sample_image),
        motion_prompt=motion_prompt,
        duration=5,
        provider="kling",
    )
    assert call_count == 1  # cached
    assert Path(res2.output_path).exists()
    assert Path(res2.output_path).read_bytes() == b"mock video data"

@pytest.mark.asyncio
async def test_cache_disabled(monkeypatch, sample_image, settings_override):
    """Verify that when enable_cache=False, caching is bypassed entirely."""
    settings = settings_override
    settings.enable_cache = False
    call_count = 0

    async def mock_generate_video(req):
        nonlocal call_count
        call_count += 1
        out = settings.work_dir / "mock_output_disabled.mp4"
        out.write_bytes(b"mock disabled video data")
        return VideoResult(
            output_path=str(out),
            duration_seconds=req.duration,
            width=1080,
            height=1920,
            fps=30,
            file_size_mb=1.2,
            provider_used=req.provider,
            cost_credits=10.0,
        )

    mock_provider = MagicMock()
    mock_provider.generate_video = mock_generate_video
    monkeypatch.setattr("video_mcp.tools.generate.KlingProvider", lambda *a, **kw: mock_provider)

    motion_prompt = "pan left"

    # First call
    res1 = await generate_video_from_image(
        image_path=str(sample_image),
        motion_prompt=motion_prompt,
        duration=5,
        provider="kling",
    )
    assert call_count == 1

    # Check cache directory contains no files
    cache_dir = settings.work_dir / ".mcp_cache"
    cached_mp4s = list(cache_dir.glob("video_*.mp4")) if cache_dir.exists() else []
    assert len(cached_mp4s) == 0

    # Second call should invoke provider again
    res2 = await generate_video_from_image(
        image_path=str(sample_image),
        motion_prompt=motion_prompt,
        duration=5,
        provider="kling",
    )
    assert call_count == 2  # bypassed
