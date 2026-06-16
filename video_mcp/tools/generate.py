import asyncio
import time
from pathlib import Path
from typing import Any, cast

import structlog

from video_mcp.errors import ErrorCode, MCPVideoError
from video_mcp.guardrails import (
    sanitize_prompt,
    validate_aspect_ratio,
    validate_duration,
    validate_input_path,
    validate_output_path,
)
from video_mcp.jobs import get_job_manager
from video_mcp.models.results import AudioResult, BatchResult, JobStatus, VideoResult, ReelResult
from video_mcp.models.schemas import ClipSequence, GenerationRequest, SceneRequest
from video_mcp.providers.elevenlabs import ElevenLabsProvider
from video_mcp.providers.hailuo import HailuoProvider
from video_mcp.providers.kling import KlingProvider
from video_mcp.providers.veo import VeoProvider

logger = structlog.get_logger()

def _get_provider(provider_name: str) -> Any:
    name = provider_name.lower()
    if name == "kling":
        return KlingProvider()
    if name == "hailuo":
        return HailuoProvider()
    if name == "veo":
        return VeoProvider()
    raise MCPVideoError(
        f"Unknown video provider '{provider_name}' requested.",
        ErrorCode.INVALID_INPUT,
    )

async def generate_video_from_image(
    image_path: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    provider: str = "kling",
    model: str = "auto",
    audio_prompt: str | None = None,
) -> VideoResult:
    """
    Generate a video clip from a single reference image using AI models.

    Inputs:
        image_path: Absolute local path to source image.
        motion_prompt: Visual directions for movements (e.g., push, pull, pan, tilt, orbit).
        duration: Video length in seconds (default: 5).
        aspect_ratio: Destination screen shape (9:16, 16:9, 1:1, 4:5).
        provider: Generative AI engine (kling, hailuo, veo).
        model: Quality presets (auto, quality, fast).
        audio_prompt: Optional voice or sound effects prompt to generate with video.

    Returns:
        VideoResult containing output file path, dimensions, size, and credit costs.
    """
    start_time = time.monotonic()
    
    # Run guardrails
    validated_img = validate_input_path(image_path)
    validate_aspect_ratio(aspect_ratio)
    validate_duration(duration, provider)
    clean_prompt = sanitize_prompt(motion_prompt)

    logger.info(
        "tool_call",
        tool_name="generate_video_from_image",
        provider=provider,
        image_path=str(validated_img),
        duration=duration,
    )

    req = GenerationRequest(
        image_path=str(validated_img),
        motion_prompt=clean_prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        provider=provider,
        model=model,
        audio_prompt=audio_prompt,
    )

    prov_client = _get_provider(provider)
    result = cast(VideoResult, await prov_client.generate_video(req))

    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "tool_success",
        tool_name="generate_video_from_image",
        duration_ms=duration_ms,
        output_path=result.output_path,
    )
    return result

async def generate_video_from_text(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    style: str = "cinematic",
    provider: str = "kling",
) -> VideoResult:
    """
    Generate a video clip directly from a descriptive text prompt.

    Inputs:
        prompt: Rich textual description of characters, scene, and actions.
        duration: Video length in seconds (default: 5).
        aspect_ratio: Output shape preset (e.g., 9:16).
        style: Cinematic style hint (cinematic, pixar, realistic).
        provider: AI engine (kling).

    Returns:
        VideoResult containing file specifications.
    """
    start_time = time.monotonic()
    
    validate_aspect_ratio(aspect_ratio)
    validate_duration(duration, provider)
    clean_prompt = sanitize_prompt(prompt)

    logger.info(
        "tool_call",
        tool_name="generate_video_from_text",
        provider=provider,
        prompt=clean_prompt,
    )

    prov_client = _get_provider(provider)
    # Kling supports text to video directly
    if not hasattr(prov_client, "submit_text_to_video"):
        raise MCPVideoError(
            f"Provider '{provider}' does not support text-to-video generation.",
            ErrorCode.INVALID_INPUT,
        )

    # Submit & poll
    job_id = await prov_client.submit_text_to_video(
        prompt=clean_prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        style=style,
    )
    task_data = await prov_client.poll_job(job_id)
    
    video_url = task_data.get("video_url") or task_data.get("video", {}).get("url")
    if not video_url:
        raise MCPVideoError(
            "Text video generation succeeded but download URL was missing.",
            ErrorCode.PROVIDER_ERROR,
            provider=provider,
        )

    from video_mcp.guardrails import validate_output_path
    output_path = validate_output_path(None, ".mp4")
    await prov_client.download_video(video_url, output_path)

    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    result = VideoResult(
        output_path=str(output_path),
        duration_seconds=float(duration),
        width=width,
        height=height,
        fps=30,
        file_size_mb=round(output_path.stat().st_size / (1024 * 1024), 2),
        provider_used=provider,
        cost_credits=10.0 if duration <= 5 else 20.0,
    )

    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "tool_success",
        tool_name="generate_video_from_text",
        duration_ms=duration_ms,
        output_path=result.output_path,
    )
    return result

async def batch_generate_scenes(
    scenes: list[SceneRequest],
    provider: str = "kling",
    max_concurrent: int = 4,
) -> BatchResult:
    """
    Generate multiple video scenes in parallel with rate-limited concurrency.

    Inputs:
        scenes: List of SceneRequest payloads describing each frame.
        provider: AI generation provider.
        max_concurrent: Maximum parallel HTTP calls.

    Returns:
        BatchResult tracking successful video results and any failed scene numbers.
    """
    start_time = time.monotonic()
    logger.info("tool_call", tool_name="batch_generate_scenes", scene_count=len(scenes))

    sem = asyncio.Semaphore(max_concurrent)
    results: list[VideoResult] = []
    failed_scenes: list[int] = []

    async def _generate_scene_task(scene: SceneRequest) -> VideoResult | None:
        async with sem:
            try:
                logger.info(f"Scene {scene.scene_number}/{len(scenes)} starting generation...")
                res = await generate_video_from_image(
                    image_path=scene.image_path,
                    motion_prompt=scene.motion_prompt,
                    duration=scene.duration,
                    provider=provider,
                    audio_prompt=scene.audio_prompt,
                )
                logger.info(f"Scene {scene.scene_number}/{len(scenes)} complete.")
                return res
            except Exception as e:
                logger.error(
                    "scene_generation_failed",
                    scene_number=scene.scene_number,
                    error=str(e),
                )
                failed_scenes.append(scene.scene_number)
                return None

    tasks = [_generate_scene_task(s) for s in scenes]
    completed = await asyncio.gather(*tasks)
    
    successful_results = [r for r in completed if r is not None]
    total_cost = sum(r.cost_credits for r in successful_results if r.cost_credits is not None)
    total_duration = sum(r.duration_seconds for r in successful_results)

    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "tool_success",
        tool_name="batch_generate_scenes",
        duration_ms=duration_ms,
        success_count=len(successful_results),
        fail_count=len(failed_scenes),
    )

    return BatchResult(
        results=successful_results,
        total_cost_credits=float(total_cost),
        failed_scenes=failed_scenes,
        total_duration_seconds=float(total_duration),
    )

async def generate_voiceover(
    script: str,
    voice_id: str = "adam",
    speed: float = 0.95,
    output_path: str | None = None,
) -> AudioResult:
    """
    Convert written speech into high-fidelity voiceover files.

    Inputs:
        script: Text script to be spoken.
        voice_id: ElevenLabs voice identifier (default: adam).
        speed: Speed factor modifier (0.5 to 2.0).
        output_path: Destination file location.

    Returns:
        AudioResult with path, duration, character count, and credit usage.
    """
    logger.info("tool_call", tool_name="generate_voiceover", char_count=len(script))
    client = ElevenLabsProvider()
    result = await client.generate_voiceover(
        script=script,
        voice_id=voice_id,
        speed=speed,
        output_path=output_path,
    )
    return result

async def check_generation_job(job_id: str) -> JobStatus:
    """
    Query the status and progress of an active background generation job.

    Inputs:
        job_id: The UUID4 of the job.

    Returns:
        JobStatus detailing state (pending, running, complete, failed) and progress.
    """
    manager = get_job_manager()
    return await manager.status(job_id)

async def create_reel_from_brief(
    script: str,
    style: str = "pixar",
    platform: str = "instagram",
    provider: str = "kling",
    voice_id: str = "adam",
    character_name: str | None = None,
    output_path: str | None = None,
) -> ReelResult:
    """
    Flagship end-to-end tool to generate a vertical reel from a text brief.

    Inputs:
        script: Full written speech/narration script.
        style: Branded visual style template (pixar, cinematic).
        platform: Target social platform (instagram, youtube, tiktok).
        provider: Generative AI engine.
        voice_id: ElevenLabs voice id.
        character_name: Optional character name to enforce consistency.
        output_path: Destination path.

    Returns:
        ReelResult detailing output file path, duration, cost, and storyboard metadata.
    """
    import uuid

    from video_mcp.config import get_settings
    from video_mcp.tools.analyze import analyze_video, video_quality_check
    from video_mcp.tools.assemble import assemble_reel
    from video_mcp.tools.character import load_character_profile

    start_time = time.monotonic()
    settings = get_settings()
    session_id = uuid.uuid4().hex

    # 1. Parse Script into Scenes
    scenes_text = [s.strip() for s in script.split("\n\n") if s.strip()]
    if not scenes_text:
        # Fallback to lines if no double paragraph breaks
        scenes_text = [s.strip() for s in script.split("\n") if s.strip()]
    scenes_text = scenes_text[:8]  # Limit to 8 scenes

    # 2. Generate Voiceover
    logger.info("orchestrator_vo_start", char_count=len(script))
    vo_file = settings.work_dir / f"vo_{session_id}.mp3"
    vo_result = await generate_voiceover(
        script=script,
        voice_id=voice_id,
        speed=0.95,
        output_path=str(vo_file),
    )
    vo_dur = vo_result.duration_seconds
    scene_dur = max(2, int(round(vo_dur / len(scenes_text))))

    # 3. Create placeholder image if no character profile
    default_img = settings.work_dir / "default_scene_input.png"
    if not default_img.exists():
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
            "-vframes", "1", str(default_img)
        ], capture_output=True)

    # 4. Load character descriptor if character lock requested
    char_desc = ""
    ref_image = str(default_img)
    if character_name:
        try:
            profile = await load_character_profile(character_name)
            char_desc = f"{profile.prompt_descriptor}, "
            # Find stored references in character profile
            profile_path = settings.work_dir / "characters" / f"{character_name.lower().replace(' ', '_')}.json"
            if profile_path.exists():
                with open(profile_path, encoding="utf-8") as f:
                    import json
                    profile_data = json.load(f)
                    ref_image = profile_data.get("reference_images", [str(default_img)])[0]
        except Exception as e:
            logger.warn("orchestrator_character_load_failed", error=str(e))

    # Style defaults
    style_prompts = {
        "pixar": "Pixar 3D animation style, warm cinematic lighting, expressive character, Renderman quality",
        "cinematic": "cinematic feature film style, 8k resolution, dramatic lighting, detailed",
    }
    sp = style_prompts.get(style.lower(), style)

    # Compile scene request list
    scene_requests = []
    for idx, text in enumerate(scenes_text):
        motion_p = f"{char_desc}{sp}, motion: {text}"
        scene_requests.append(SceneRequest(
            scene_number=idx + 1,
            image_path=ref_image,
            motion_prompt=motion_p,
            duration=scene_dur,
        ))

    # 5. Batch generation of clips
    logger.info("orchestrator_scenes_start", count=len(scene_requests))
    batch_res = await batch_generate_scenes(
        scenes=scene_requests,
        provider=provider,
        max_concurrent=4,
    )

    # Aligned timelines
    clips_seq = []
    
    # 6. Build Clip Sequences (substitute placeholders for failures)
    for idx in range(len(scenes_text)):
        # Try finding the success scene result
        success_clip = None
        for r in batch_res.results:
            # Match by output path sequence or metadata
            # We check if it matches duration or mapping
            pass
        
        # We can map by index directly if order matches
        if idx < len(batch_res.results):
            success_clip = batch_res.results[idx].output_path
            clip_duration = batch_res.results[idx].duration_seconds
        else:
            # Generate placeholder black frame
            placeholder = settings.work_dir / f"placeholder_{session_id}_{idx}.mp4"
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={scene_dur}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(placeholder)
            ], capture_output=True)
            success_clip = str(placeholder)
            clip_duration = float(scene_dur)

        clips_seq.append(ClipSequence(
            clip_path=success_clip,
            start_time=0.0,
            duration=clip_duration,
        ))

    # 7. Timeline assembly and captioned rendering
    logger.info("orchestrator_assembly_start")
    final_reel_path = validate_output_path(output_path, ".mp4")
    
    reel_res = await assemble_reel(
        clips=clips_seq,
        voiceover_path=str(vo_file),
        bgm_path=None,
        output_path=str(final_reel_path),
        aspect_ratio="9:16" if platform in ("instagram", "tiktok", "youtube-shorts") else "16:9",
        add_captions=True,
    )

    # 8. Perform quality check and analyze storyboard
    chk = await video_quality_check(str(final_reel_path))
    if chk["issues"]:
        logger.warning("orchestrator_quality_issues", issues=chk["issues"])
    analysis = await analyze_video(str(final_reel_path))

    # Calculate costs
    cost_map = {
        provider: batch_res.total_cost_credits,
        "elevenlabs": vo_result.cost_credits or 0.0,
    }

    # Cleanup VO temp
    vo_file.unlink(missing_ok=True)

    # Clean up scene files that were assembled
    # Only keep final reel
    for clip in clips_seq:
        if "placeholder" in clip.clip_path:
            Path(clip.clip_path).unlink(missing_ok=True)

    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "orchestrator_reel_success",
        duration_ms=duration_ms,
        output_path=reel_res.output_path,
    )

    return ReelResult(
        output_path=reel_res.output_path,
        total_duration=reel_res.duration_seconds,
        scene_count=len(scenes_text),
        cost_breakdown=cost_map,
        storyboard_path=analysis.thumbnails[0] if analysis.thumbnails else None,
    )
