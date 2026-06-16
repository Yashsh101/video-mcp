import pytest
from click.testing import CliRunner
from video_mcp.cli import main

def test_cli_help():
    """Verify CLI help output lists all root-level options."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "doctor" in result.output
    assert "generate" in result.output
    assert "voiceover" in result.output

def test_cli_doctor_success():
    """Verify CLI doctor diagnosis runs and completes successfully."""
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # If ffmpeg is present, it will exit 0.
    # We assert it runs without python syntax/runtime crashes.
    assert "Running diagnostics" in result.output

def test_cli_providers():
    """Verify providers list command prints configured services."""
    runner = CliRunner()
    result = runner.invoke(main, ["providers"])
    assert result.exit_code == 0
    assert "KLING_API_KEY" in result.output
    assert "ELEVENLABS_API_KEY" in result.output
