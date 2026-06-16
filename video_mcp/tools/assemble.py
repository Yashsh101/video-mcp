import subprocess
import time
import uuid
from pathlib import Path

import structlog

from video_mcp.config import get_settings
from video_mcp.errors import ErrorCode, MCPVideoError
from video_mcp.guardrails import validate_input_path, validate_output_path
from video_mcp.models.results import VideoResult
from video_mcp.models.schemas import ClipSequence
from video_mcp.tools.edit import add_subtitles, get_video_properties

logger = structlog.get_logger()

def _has_audio_stream(path: Path) -> bool:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=codec_name", "-of", "csv=p=0",
            str(path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return len(res.stdout.strip()) > 0
    except Exception:
        return False

async def assemble_reel(
    clips: list[ClipSequence],
    voiceover_path: str,
    bgm_path: str | None = None,
    bgm_volume: float = 0.12,
    output_path: str | None = None,
    aspect_ratio: str = "9:16",
    add_captions: bool = True,
) -> VideoResult:
    """
    Stitch multiple video clips together, align them to a voiceover, and add background music.

    Inputs:
        clips: List of ClipSequence specifications containing clip paths and timings.
        voiceover_path: Primary spoken voiceover track.
        bgm_path: Optional background music track.
        bgm_volume: Volume multiplier for background music (default: 0.12).
        output_path: Output reel file destination.
        aspect_ratio: Target aspect ratio (9:16, 16:9).
        add_captions: Burn-in subtitles if a corresponding SRT is found.

    Returns:
        VideoResult containing the completed video file information.
    """
    start_time = time.monotonic()
    settings = get_settings()
    
    # Validate main inputs
    validated_vo = validate_input_path(voiceover_path)
    validated_bgm = validate_input_path(bgm_path) if bgm_path else None
    validated_out = validate_output_path(output_path, ".mp4")

    if not clips:
        raise MCPVideoError("Cannot assemble reel with empty clip list.", ErrorCode.INVALID_INPUT)

    session_id = uuid.uuid4().hex
    temp_clips: list[Path] = []

    # Get target dimensions
    tw, th = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

    try:
        # STEP 1: Pre-process each clip (Trim, Resize, and guarantee Audio track)
        for i, clip in enumerate(clips):
            val_path = validate_input_path(clip.clip_path)
            temp_out = settings.work_dir / f"temp_{session_id}_{i}.mp4"
            
            has_audio = _has_audio_stream(val_path)
            
            # Prepare ffmpeg command
            # Crop to fit + trim
            if has_audio:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{clip.start_time:.3f}",
                    "-t", f"{clip.duration:.3f}",
                    "-i", str(val_path),
                    "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    str(temp_out)
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{clip.start_time:.3f}",
                    "-t", f"{clip.duration:.3f}",
                    "-i", str(val_path),
                    "-f", "lavfi", "-i", "anullsrc",
                    "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}",
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-shortest",
                    str(temp_out)
                ]

            logger.info("process_clip_before_concat", clip_index=i, cmd=cmd)
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise MCPVideoError(
                    f"Preprocessing failed for clip {i}: {res.stderr}",
                    ErrorCode.ASSEMBLY_FAILED,
                )
            temp_clips.append(temp_out)

        # STEP 2: Concat the aligned clips
        concat_out = settings.work_dir / f"concat_{session_id}.mp4"
        
        # Build concat command
        cmd_concat = ["ffmpeg", "-y"]
        for tc in temp_clips:
            cmd_concat += ["-i", str(tc)]
            
        filter_str = "".join(f"[{i}:v][{i}:a]" for i in range(len(temp_clips)))
        filter_str += f"concat=n={len(temp_clips)}:v=1:a=1[v][a]"
        
        cmd_concat += [
            "-filter_complex", filter_str,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(concat_out)
        ]
        
        logger.info("concat_clips", cmd=cmd_concat)
        res = subprocess.run(cmd_concat, capture_output=True, text=True)
        if res.returncode != 0:
            raise MCPVideoError(
                f"Concat filter failed: {res.stderr}",
                ErrorCode.ASSEMBLY_FAILED,
            )

        # STEP 3: Replace original clip audio with Voiceover + background music mix
        audio_mixed_out = settings.work_dir / f"mixed_{session_id}.mp4"
        
        if validated_bgm:
            cmd_audio = [
                "ffmpeg", "-y",
                "-i", str(concat_out),
                "-i", str(validated_vo),
                "-i", str(validated_bgm),
                "-filter_complex", f"[1:a]volume=1.0[vo];[2:a]volume={bgm_volume}[bg];[vo][bg]amix=inputs=2:duration=first[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                str(audio_mixed_out)
            ]
        else:
            cmd_audio = [
                "ffmpeg", "-y",
                "-i", str(concat_out),
                "-i", str(validated_vo),
                "-filter_complex", "[1:a]volume=1.0[aout]",
                "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                str(audio_mixed_out)
            ]
            
        logger.info("mix_audio_to_concatenated_video", cmd=cmd_audio)
        res = subprocess.run(cmd_audio, capture_output=True, text=True)
        if res.returncode != 0:
            raise MCPVideoError(
                f"Audio mixing failed: {res.stderr}",
                ErrorCode.ASSEMBLY_FAILED,
            )

        # STEP 4: Burn-in captions if requested and .srt is present
        srt_file = validated_vo.with_suffix(".srt")
        if add_captions and srt_file.exists():
            await add_subtitles(
                video_path=str(audio_mixed_out),
                srt_path=str(srt_file),
                output_path=str(validated_out),
            )
        else:
            # Copy output to final location
            import shutil
            shutil.copy(audio_mixed_out, validated_out)

    finally:
        # Cleanup temporary files
        for tc in temp_clips:
            tc.unlink(missing_ok=True)
        (settings.work_dir / f"concat_{session_id}.mp4").unlink(missing_ok=True)
        (settings.work_dir / f"mixed_{session_id}.mp4").unlink(missing_ok=True)

    props = get_video_properties(validated_out)
    duration_ms = (time.monotonic() - start_time) * 1000
    
    logger.info(
        "tool_success",
        tool_name="assemble_reel",
        duration_ms=duration_ms,
        output_path=str(validated_out),
    )

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
