import pytest
import shutil
from pathlib import Path
from video_mcp.models.schemas import ClipSequence
from video_mcp.tools.edit import trim_clip, add_subtitles, resize_to_platform
from video_mcp.tools.assemble import assemble_reel

# Check if FFmpeg is installed and accessible on system PATH
ffmpeg_missing = shutil.which("ffmpeg") is None

@pytest.mark.asyncio
@pytest.mark.skipif(ffmpeg_missing, reason="FFmpeg executable is not available on PATH")
async def test_trim_clip(sample_video):
    """Verify trim_clip cuts video duration correctly."""
    out = await trim_clip(
        input_path=str(sample_video),
        start_time=0.0,
        duration=0.5,
    )
    assert Path(out.output_path).exists()
    assert out.duration_seconds <= 1.0  # Sample is 1s, trim length 0.5s

@pytest.mark.asyncio
@pytest.mark.skipif(ffmpeg_missing, reason="FFmpeg executable is not available on PATH")
async def test_assemble_reel(sample_video, sample_audio):
    """Verify assemble_reel stitches clips, merges voiceover, and finishes execution."""
    clips = [
        ClipSequence(clip_path=str(sample_video), start_time=0.0, duration=0.5),
        ClipSequence(clip_path=str(sample_video), start_time=0.0, duration=0.5),
    ]
    out = await assemble_reel(
        clips=clips,
        voiceover_path=str(sample_audio),
        bgm_path=None,
        add_captions=False,
    )
    assert Path(out.output_path).exists()
    assert out.duration_seconds > 0.0

@pytest.mark.asyncio
@pytest.mark.skipif(ffmpeg_missing, reason="FFmpeg executable is not available on PATH")
async def test_resize_to_platform(sample_video):
    """Verify resize_to_platform center crops to 1080x1920 vertical layout."""
    out = await resize_to_platform(
        input_path=str(sample_video),
        platform="instagram-reel",
    )
    assert Path(out.output_path).exists()
    assert out.width == 1080
    assert out.height == 1920
