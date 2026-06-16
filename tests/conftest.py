import pytest
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from video_mcp.config import Settings, get_settings
from video_mcp.models.results import VideoResult, AudioResult

@pytest.fixture(autouse=True)
def settings_override(tmp_path, monkeypatch):
    """Overrides workspace directory to a temporary pytest path and configures default settings."""
    get_settings.cache_clear()
    work_dir = tmp_path / "work_dir"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    mock_settings = Settings(
        kling_api_key="mock-kling-key",
        elevenlabs_api_key="mock-elevenlabs-key",
        hailuo_api_key="mock-hailuo-key",
        veo_api_key="mock-veo-key",
        work_dir=work_dir,
        max_file_size_mb=10,
        default_provider="kling",
        log_level="DEBUG"
    )
    monkeypatch.setattr("video_mcp.config.get_settings", lambda: mock_settings)
    monkeypatch.setenv("VIDEO_MCP_WORK_DIR", str(work_dir))
    return mock_settings

@pytest.fixture
def sample_image():
    """Generates a small test PNG image using ffmpeg or mock bytes inside the active work_dir."""
    settings = get_settings()
    p = settings.work_dir / "test_image.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    
    if shutil.which("ffmpeg"):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=1080x1920",
            "-vframes", "1", str(p)
        ], capture_output=True)
    else:
        # Fallback to dummy PNG bytes
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return p

@pytest.fixture
def sample_video():
    """Generates a tiny valid 1-second MP4 test video using ffmpeg or mock bytes inside the active work_dir."""
    settings = get_settings()
    p = settings.work_dir / "test_video.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    
    if shutil.which("ffmpeg"):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=1080x1920:rate=30",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)
        ], capture_output=True)
    else:
        # Fallback to dummy MP4 bytes
        p.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 100)
    return p

@pytest.fixture
def sample_audio():
    """Generates a tiny valid 1-second MP3 test audio using ffmpeg or mock bytes inside the active work_dir."""
    settings = get_settings()
    p = settings.work_dir / "test_audio.mp3"
    p.parent.mkdir(parents=True, exist_ok=True)
    
    if shutil.which("ffmpeg"):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:a", "libmp3lame", str(p)
        ], capture_output=True)
    else:
        # Fallback to dummy MP3 bytes
        p.write_bytes(b"ID3" + b"\x00" * 100)
    return p

@pytest.fixture
def mock_kling_provider(monkeypatch):
    """Mocks KlingProvider video generator methods where they are imported."""
    mock = MagicMock()
    
    # Mock async method generate_video to create a physical file on disk
    async def mock_generate_video(req):
        settings = get_settings()
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

    mock.generate_video = AsyncMock(side_effect=mock_generate_video)
    # Mock where imported in generate.py
    monkeypatch.setattr("video_mcp.tools.generate.KlingProvider", lambda *a, **kw: mock)
    monkeypatch.setattr("video_mcp.providers.kling.KlingProvider", lambda *a, **kw: mock)
    return mock

@pytest.fixture
def mock_elevenlabs_provider(monkeypatch):
    """Mocks ElevenLabs TTS generator methods where they are imported."""
    mock = MagicMock()
    
    # Mock async generate_voiceover dynamically to match input script length and create physical file
    async def mock_generate_voiceover(script, voice_id="adam", speed=0.95, output_path=None):
        settings = get_settings()
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

    mock.generate_voiceover = AsyncMock(side_effect=mock_generate_voiceover)
    # Mock where imported in generate.py and audio.py
    monkeypatch.setattr("video_mcp.tools.generate.ElevenLabsProvider", lambda *a, **kw: mock)
    monkeypatch.setattr("video_mcp.providers.elevenlabs.ElevenLabsProvider", lambda *a, **kw: mock)
    return mock
