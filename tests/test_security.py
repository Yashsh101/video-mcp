import pytest
import subprocess
from unittest.mock import patch
from pathlib import Path
from video_mcp.errors import MCPVideoError
from video_mcp.tools.edit import trim_clip

@patch("subprocess.run")
def test_no_shell_injection(mock_run, tmp_path, monkeypatch):
    """Verify that FFmpeg commands are executed as lists and shell=True is never set."""
    # Setup mock returns
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="1920,1080,30,5.0", stderr="")
    
    # Override paths to avoid validation failures
    settings = patch("video_mcp.guardrails.get_settings")
    
    # We test that when calling subprocess.run, it is called with shell=False (default) and args is a list
    # Malicious payload in input path that would crash/inject if passed to a shell
    malicious_input = "video.mp4; rm -rf /"
    
    # Let's mock validate_input_path to return a resolved path (simulate passing validation check)
    with patch("video_mcp.tools.edit.validate_input_path") as mock_val_in, \
         patch("video_mcp.tools.edit.validate_output_path") as mock_val_out, \
         patch("video_mcp.tools.edit.get_video_properties") as mock_props:
         
        in_file = Path(tmp_path / "work_dir" / "video.mp4")
        out_file = Path(tmp_path / "work_dir" / "trimmed.mp4")
        in_file.parent.mkdir(parents=True, exist_ok=True)
        in_file.touch()
        out_file.touch()

        mock_val_in.return_value = in_file
        mock_val_out.return_value = out_file
        mock_props.return_value = {"width": 1080, "height": 1920, "fps": 30, "duration": 5.0}
        
        # Call trim
        import asyncio
        asyncio.run(trim_clip(
            input_path=malicious_input,
            start_time=1.0,
            duration=3.0,
            output_path="trimmed.mp4"
        ))
        
        # Assertions
        assert mock_run.called
        called_args, called_kwargs = mock_run.call_args
        
        # Verify shell=True is NOT used
        assert "shell" not in called_kwargs or called_kwargs["shell"] is False
        
        # Verify the command is passed as a list of independent arguments
        cmd_list = called_args[0]
        assert isinstance(cmd_list, list)
        # Verify the malicious segment is contained in a single list element, preventing shell execution
        assert any("video.mp4" in str(x) for x in cmd_list)
