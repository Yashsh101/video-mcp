import pytest
from pathlib import Path
from video_mcp.errors import MCPVideoError
from video_mcp.guardrails import (
    validate_input_path,
    validate_output_path,
    validate_file_size,
    validate_aspect_ratio,
    sanitize_prompt,
)
from video_mcp.config import get_settings

def test_validate_input_path_traversal():
    """Verify validate_input_path rejects path traversal outside the WORK_DIR."""
    with pytest.raises(MCPVideoError) as exc_info:
        validate_input_path("../../../etc/passwd")
    assert "Path violation" in str(exc_info.value)

def test_validate_input_path_outside_workdir():
    """Verify absolute paths outside WORK_DIR are rejected."""
    with pytest.raises(MCPVideoError) as exc_info:
        validate_input_path("/etc/passwd")
    assert "Path violation" in str(exc_info.value)

def test_validate_input_path_success(sample_video):
    """Verify input path validation succeeds on local workspace files."""
    path = validate_input_path(str(sample_video))
    assert path.exists()

def test_validate_output_path_generation():
    """Verify output path is auto-generated inside WORK_DIR if None."""
    settings = get_settings()
    out = validate_output_path(None, ".mp4")
    assert out.parent == settings.work_dir.resolve()
    assert out.name.endswith(".mp4")

def test_validate_file_size(sample_video):
    """Verify validate_file_size raises if file exceeds size limitations."""
    settings = get_settings()
    settings.max_file_size_mb = 0  # Forces everything to be oversized
    
    with pytest.raises(MCPVideoError) as exc_info:
        validate_file_size(sample_video)
    assert "exceeds limit" in str(exc_info.value)

def test_validate_aspect_ratio():
    """Verify aspect ratio filters match standard formats."""
    validate_aspect_ratio("9:16")
    validate_aspect_ratio("1:1")
    
    with pytest.raises(MCPVideoError) as exc_info:
        validate_aspect_ratio("5:7")
    assert "Invalid aspect ratio" in str(exc_info.value)

def test_sanitize_prompt():
    """Verify prompt sanitizer cleans control characters and null bytes."""
    prompt = "Cinematic video\x00 with null bytes and control \x01 chars."
    sanitized = sanitize_prompt(prompt)
    assert "\x00" not in sanitized
    assert "\x01" not in sanitized
    assert sanitized.startswith("Cinematic video")
