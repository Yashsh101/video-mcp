import subprocess
import time
from pathlib import Path
from typing import Any, cast

import structlog

from video_mcp.errors import ErrorCode, MCPVideoError
from video_mcp.guardrails import validate_input_path, validate_output_path
from video_mcp.models.results import AudioResult, VideoResult
from video_mcp.providers.elevenlabs import get_audio_duration

logger = structlog.get_logger()

def _has_video_stream(path: Path) -> bool:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v",
            "-show_entries", "stream=codec_name", "-of", "csv=p=0",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return len(res.stdout.strip()) > 0
    except Exception:
        return False

async def normalize_audio(
    input_path: str,
    target_lufs: float = -14.0,
    output_path: str | None = None,
) -> VideoResult:
    """
    Normalize the audio track of a video or audio file to EBU R128 (-14 LUFS) standards.

    Inputs:
        input_path: Path to source file (MP3, WAV, MP4, etc.).
        target_lufs: Loudness target in LUFS (default: -14.0).
        output_path: Path to write normalized file.

    Returns:
        VideoResult referencing the output.
    """
    start_time = time.monotonic()
    validated_in = validate_input_path(input_path)
    
    # Check suffix to decide format
    suffix = validated_in.suffix
    validated_out = validate_output_path(output_path, suffix)

    is_video = _has_video_stream(validated_in)
    
    # Construct FFmpeg command
    cmd = ["ffmpeg", "-y", "-i", str(validated_in)]
    
    # Apply loudnorm filter
    cmd += ["-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"]
    
    if is_video:
        # Copy video codec without re-encoding, encode audio to aac
        cmd += ["-c:v", "copy", "-c:a", "aac", str(validated_out)]
    else:
        # Audio file
        codec = "libmp3lame" if suffix == ".mp3" else "pcm_s16le" if suffix == ".wav" else "aac"
        cmd += ["-c:a", codec, str(validated_out)]

    logger.info("audio_normalization_start", cmd=cmd)
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg audio normalization failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    duration_ms = (time.monotonic() - start_time) * 1000
    
    # Query properties
    width, height = (1080, 1920) if is_video else (0, 0)
    return VideoResult(
        output_path=str(validated_out),
        duration_seconds=get_audio_duration(validated_out),
        width=width,
        height=height,
        fps=30 if is_video else 0,
        file_size_mb=round(validated_out.stat().st_size / (1024 * 1024), 2),
        provider_used="ffmpeg",
        cost_credits=0.0,
    )

async def extract_audio(
    video_path: str,
    format: str = "mp3",
    output_path: str | None = None,
) -> AudioResult:
    """
    Extract the audio track from a video file.

    Inputs:
        video_path: Source video file path.
        format: Output audio format (mp3 or wav).
        output_path: File destination.

    Returns:
        AudioResult with specifications.
    """
    validated_in = validate_input_path(video_path)
    suffix = f".{format.lower().strip('.')}"
    validated_out = validate_output_path(output_path, suffix)

    cmd = ["ffmpeg", "-y", "-i", str(validated_in), "-vn"]
    if format == "mp3":
        cmd += ["-c:a", "libmp3lame", "-q:a", "2"]
    else:
        cmd += ["-c:a", "pcm_s16le"]
    cmd.append(str(validated_out))

    logger.info("audio_extraction_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg audio extraction failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    return AudioResult(
        output_path=str(validated_out),
        duration_seconds=get_audio_duration(validated_out),
        voice_id="extracted",
        character_count=0,
        cost_credits=0.0,
    )

async def mix_audio_tracks(
    tracks: list[dict[str, Any]],
    output_path: str | None = None,
) -> AudioResult:
    """
    Mix multiple audio tracks together with independent volume controls and offsets.

    Inputs:
        tracks: List of dicts: [{"path": str, "volume": float, "offset_seconds": float}]
        output_path: Destination path.

    Returns:
        AudioResult detailing the mixed track.
    """
    if not tracks:
        raise MCPVideoError("No audio tracks provided to mix.", ErrorCode.INVALID_INPUT)

    # Validate all tracks
    validated_tracks = []
    for t in tracks:
        p = validate_input_path(t["path"])
        validated_tracks.append({
            "path": p,
            "volume": float(t.get("volume", 1.0)),
            "offset_seconds": float(t.get("offset_seconds", 0.0))
        })

    # Output defaults to MP3
    validated_out = validate_output_path(output_path, ".mp3")

    cmd = ["ffmpeg", "-y"]
    for t in validated_tracks:
        cmd += ["-i", str(t["path"])]

    # Build filter complex
    filter_inputs = ""
    for i, t in enumerate(validated_tracks):
        vol = cast(float, t["volume"])
        offset = cast(float, t["offset_seconds"])
        delay_ms = int(offset * 1000)
        
        # Apply delay if positive, then volume
        if delay_ms > 0:
            filter_inputs += f"[{i}:a]adelay={delay_ms}|{delay_ms},volume={vol}[a{i}];"
        else:
            filter_inputs += f"[{i}:a]volume={vol}[a{i}];"

    mix_inputs = "".join(f"[a{i}]" for i in range(len(validated_tracks)))
    filter_complex = f"{filter_inputs}{mix_inputs}amix=inputs={len(validated_tracks)}:duration=longest"

    cmd += ["-filter_complex", filter_complex, "-c:a", "libmp3lame", "-q:a", "2", str(validated_out)]

    logger.info("audio_mix_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg audio mixing failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    return AudioResult(
        output_path=str(validated_out),
        duration_seconds=get_audio_duration(validated_out),
        voice_id="mixed",
        character_count=0,
        cost_credits=0.0,
    )
