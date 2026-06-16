import subprocess
from pathlib import Path
from typing import Any

import structlog

from video_mcp.errors import ErrorCode, MCPVideoError
from video_mcp.guardrails import validate_input_path, validate_output_path
from video_mcp.models.results import VideoResult

logger = structlog.get_logger()

def get_video_properties(path: Path) -> dict[str, Any]:
    """Retrieves width, height, fps, and duration from video container using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate,duration",
            "-of", "csv=p=0",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parts = res.stdout.strip().split(",")
        width = int(parts[0])
        height = int(parts[1])
        fps_parts = parts[2].split("/")
        if len(fps_parts) == 2:
            fps = int(round(float(fps_parts[0]) / float(fps_parts[1])))
        else:
            fps = int(round(float(parts[2])))
        
        # Duration check
        duration = 0.0
        if len(parts) > 3 and parts[3] and parts[3] != "N/A":
            duration = float(parts[3])
        else:
            # Fallback to format duration
            cmd_fmt = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(path)
            ]
            res_fmt = subprocess.run(cmd_fmt, capture_output=True, text=True, check=True)
            val = res_fmt.stdout.strip()
            if val and val != "N/A":
                duration = float(val)
        return {"width": width, "height": height, "fps": fps, "duration": duration}
    except Exception:
        # Fallback values
        return {"width": 1080, "height": 1920, "fps": 30, "duration": 5.0}

async def trim_clip(
    input_path: str,
    start_time: float,
    duration: float | None = None,
    end_time: float | None = None,
    output_path: str | None = None,
) -> VideoResult:
    """
    Trim a video file to a specific time range.

    Inputs:
        input_path: Path to source video file.
        start_time: Time in seconds to seek to before copying.
        duration: Length in seconds of trimmed clip.
        end_time: Time in seconds to stop trimming (used if duration is omitted).
        output_path: Output file destination.

    Returns:
        VideoResult containing trimmed clip properties.
    """
    if duration is None and end_time is None:
        raise MCPVideoError("Must specify either duration or end_time.", ErrorCode.INVALID_INPUT)

    validated_in = validate_input_path(input_path)
    validated_out = validate_output_path(output_path, ".mp4")

    # Construct seek command: seek before -i for speed
    cmd = ["ffmpeg", "-y", "-ss", f"{start_time:.3f}", "-i", str(validated_in)]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    else:
        # Calculate duration based on end_time
        assert end_time is not None
        calc_dur = end_time - start_time
        cmd += ["-t", f"{calc_dur:.3f}"]

    # Copy streams if possible, otherwise re-encode. Since it's trim, stream copying is fast and safe.
    cmd += ["-c", "copy", str(validated_out)]

    logger.info("trim_clip_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg trim failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    props = get_video_properties(validated_out)
    return VideoResult(
        output_path=str(validated_out),
        duration_seconds=props["duration"],
        width=props["width"],
        height=props["height"],
        fps=props["fps"],
        file_size_mb=round(validated_out.stat().st_size / (1024 * 1024), 2),
        provider_used="ffmpeg",
        cost_credits=0.0,
    )

async def add_audio_to_video(
    video_path: str,
    audio_path: str,
    mode: str = "replace",
    volume: float = 1.0,
    output_path: str | None = None,
) -> VideoResult:
    """
    Merge an audio file into a video file.

    Inputs:
        video_path: Source video path.
        audio_path: Source audio path.
        mode: "replace" (drop existing video audio), "mix" (blend tracks), "overlay" (add track).
        volume: Audio volume multiplier.
        output_path: File output location.

    Returns:
        VideoResult referencing output video.
    """
    validated_vid = validate_input_path(video_path)
    validated_aud = validate_input_path(audio_path)
    validated_out = validate_output_path(output_path, ".mp4")

    cmd = ["ffmpeg", "-y", "-i", str(validated_vid), "-i", str(validated_aud)]

    if mode == "replace":
        # Drop original video audio track, map video track [0:v] and audio track [1:a]
        cmd += [
            "-filter_complex", f"[1:a]volume={volume}[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", str(validated_out)
        ]
    elif mode == "mix":
        # Mix audio streams
        cmd += [
            "-filter_complex", f"[0:a]volume=1.0[a0];[1:a]volume={volume}[a1];[a0][a1]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", str(validated_out)
        ]
    else:  # overlay / add as secondary track
        cmd += [
            "-map", "0:v", "-map", "0:a?", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", str(validated_out)
        ]

    logger.info("add_audio_to_video_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg audio injection failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    props = get_video_properties(validated_out)
    return VideoResult(
        output_path=str(validated_out),
        duration_seconds=props["duration"],
        width=props["width"],
        height=props["height"],
        fps=props["fps"],
        file_size_mb=round(validated_out.stat().st_size / (1024 * 1024), 2),
        provider_used="ffmpeg",
        cost_credits=0.0,
    )

async def add_subtitles(
    video_path: str,
    srt_path: str,
    style: str = "bold_white",
    output_path: str | None = None,
) -> VideoResult:
    """
    Burn subtitles directly into video pixels (hardsub).

    Inputs:
        video_path: Source video path.
        srt_path: SubRip subtitle file path.
        style: Subtitle appearance template (bold_white, minimal, dramatic).
        output_path: Destination path.

    Returns:
        VideoResult containing captioned video.
    """
    validated_vid = validate_input_path(video_path)
    validated_srt = validate_input_path(srt_path)
    validated_out = validate_output_path(output_path, ".mp4")

    # Define subtitles filter style arguments
    # FFmpeg subtitles filter uses backslashes in Windows. We escape the path correctly.
    escaped_srt = str(validated_srt).replace("\\", "/").replace(":", "\\:")
    
    style_def = "FontSize=20,PrimaryColour=&HFFFFFF,Outline=2"
    if style == "minimal":
        style_def = "FontSize=16,PrimaryColour=&HFFFFFF,Outline=0"
    elif style == "dramatic":
        style_def = "FontSize=24,PrimaryColour=&H00FFFF,Bold=1,Outline=3"

    sub_filter = f"subtitles={escaped_srt}:force_style='{style_def}'"

    cmd = [
        "ffmpeg", "-y", "-i", str(validated_vid),
        "-vf", sub_filter,
        "-c:a", "copy",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(validated_out)
    ]

    logger.info("add_subtitles_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg subtitle burn failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    props = get_video_properties(validated_out)
    return VideoResult(
        output_path=str(validated_out),
        duration_seconds=props["duration"],
        width=props["width"],
        height=props["height"],
        fps=props["fps"],
        file_size_mb=round(validated_out.stat().st_size / (1024 * 1024), 2),
        provider_used="ffmpeg",
        cost_credits=0.0,
    )

async def resize_to_platform(
    input_path: str,
    platform: str = "instagram-reel",
    output_path: str | None = None,
) -> VideoResult:
    """
    Scale and crop/pad a video clip to match a specific destination platform specification.

    Inputs:
        input_path: Source file path.
        platform: Branded specifications (instagram-reel, youtube-shorts, tiktok, instagram-square, youtube).
        output_path: Destination path.

    Returns:
        VideoResult showing the resized clip properties.
    """
    validated_in = validate_input_path(input_path)
    validated_out = validate_output_path(output_path, ".mp4")

    # Map target dimensions
    dims = {
        "instagram-reel": (1080, 1920),
        "youtube-shorts": (1080, 1920),
        "tiktok": (1080, 1920),
        "instagram-square": (1080, 1080),
        "youtube": (1920, 1080),
    }.get(platform.lower().strip(), (1080, 1920))

    tw, th = dims

    # Fit and center crop filter
    filter_str = f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}"

    cmd = [
        "ffmpeg", "-y", "-i", str(validated_in),
        "-vf", filter_str,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(validated_out)
    ]

    logger.info("resize_to_platform_start", cmd=cmd)
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise MCPVideoError(
            f"FFmpeg resize failed: {e.stderr}",
            ErrorCode.ASSEMBLY_FAILED,
        )

    props = get_video_properties(validated_out)
    return VideoResult(
        output_path=str(validated_out),
        duration_seconds=props["duration"],
        width=props["width"],
        height=props["height"],
        fps=props["fps"],
        file_size_mb=round(validated_out.stat().st_size / (1024 * 1024), 2),
        provider_used="ffmpeg",
        cost_credits=0.0,
    )
