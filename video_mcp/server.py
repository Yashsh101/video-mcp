from typing import Any

import structlog
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from video_mcp.config import get_settings
from video_mcp.models.results import (
    AnalysisResult,
    AudioResult,
    BatchResult,
    CharacterProfile,
    JobStatus,
    ReelResult,
    VideoResult,
)
from video_mcp.models.schemas import ClipSequence, SceneRequest

logger = structlog.get_logger()

# Initialize FastMCP Server
mcp = FastMCP(
    "video-mcp",
    version="0.1.0",
)

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "video-mcp", "version": "0.1.0"})

# Startup hook
@mcp.resource("video_mcp://help")
def get_help() -> str:
    """Returns documentation and quick-start tips."""
    return (
        "Video-MCP is an AI-native video generation Model Context Protocol server.\n"
        "To get started, try calling create_reel_from_brief with a narrative script."
    )

@mcp.resource("video_mcp://providers")
def get_providers() -> str:
    """Returns configured video and audio providers status."""
    settings = get_settings()
    kling = "Configured" if settings.kling_api_key else "Missing"
    el = "Configured" if settings.elevenlabs_api_key else "Missing"
    hailuo = "Configured" if settings.hailuo_api_key else "Missing"
    veo = "Configured" if settings.veo_api_key else "Missing"
    return f"Kling: {kling}\nElevenLabs: {el}\nHailuo: {hailuo}\nVeo: {veo}"

@mcp.resource("video_mcp://credits")
def get_credits() -> str:
    """Returns estimated credits statement."""
    return "Check provider balances by initializing provider wrappers."

@mcp.prompt("create_reel_prompt")
def create_reel_prompt(
    topic: str,
    style: str = "pixar",
    duration: int = 60,
    platform: str = "instagram",
) -> str:
    """Prompt template to construct script briefs."""
    return (
        f"You are a viral reel script writer. Write a structured script about {topic} "
        f"suited for an {platform} reel. Total duration target is {duration} seconds. "
        f"Describe 6-8 visual scenes styled in {style} using [SCENE] or paragraph breaks."
    )

# 1. create_reel_from_brief
@mcp.tool()
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
    Generate a full captioned short-form video reel from a narration script.
    
    This is the flagship orchestrator tool that handles voiceover generation,
    scene decomposition, parallel clip creation, timeline stitching, and captions.
    """
    from video_mcp.tools.generate import create_reel_from_brief as _impl
    return await _impl(
        script=script,
        style=style,
        platform=platform,
        provider=provider,
        voice_id=voice_id,
        character_name=character_name,
        output_path=output_path,
    )

# 2. generate_video_from_image
@mcp.tool()
async def generate_video_from_image(
    image_path: str,
    motion_prompt: str,
    duration: int = 5,
    aspect_ratio: str = "9:16",
    provider: str = "kling",
    model: str = "auto",
    audio_prompt: str | None = None,
) -> VideoResult:
    """Generate a short video clip from an input image using Kling, Hailuo, or Veo."""
    from video_mcp.tools.generate import generate_video_from_image as _impl
    return await _impl(
        image_path=image_path,
        motion_prompt=motion_prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        provider=provider,
        model=model,
        audio_prompt=audio_prompt,
    )

# 3. generate_voiceover
@mcp.tool()
async def generate_voiceover(
    script: str,
    voice_id: str = "adam",
    speed: float = 0.95,
    output_path: str | None = None,
) -> AudioResult:
    """Generate professional Text-to-Speech audio voiceover using ElevenLabs."""
    from video_mcp.tools.generate import generate_voiceover as _impl
    return await _impl(
        script=script,
        voice_id=voice_id,
        speed=speed,
        output_path=output_path,
    )

# 4. batch_generate_scenes
@mcp.tool()
async def batch_generate_scenes(
    scenes: list[SceneRequest],
    provider: str = "kling",
    max_concurrent: int = 4,
) -> BatchResult:
    """Submit and process multiple scene generation requests concurrently with rate limits."""
    from video_mcp.tools.generate import batch_generate_scenes as _impl
    return await _impl(
        scenes=scenes,
        provider=provider,
        max_concurrent=max_concurrent,
    )

# 5. assemble_reel
@mcp.tool()
async def assemble_reel(
    clips: list[ClipSequence],
    voiceover_path: str,
    bgm_path: str | None = None,
    bgm_volume: float = 0.12,
    output_path: str | None = None,
    aspect_ratio: str = "9:16",
    add_captions: bool = True,
) -> VideoResult:
    """Concatenate video clips, mix audio tracks, and burn-in subtitle captions."""
    from video_mcp.tools.assemble import assemble_reel as _impl
    return await _impl(
        clips=clips,
        voiceover_path=voiceover_path,
        bgm_path=bgm_path,
        bgm_volume=bgm_volume,
        output_path=output_path,
        aspect_ratio=aspect_ratio,
        add_captions=add_captions,
    )

# 6. generate_scene_with_character
@mcp.tool()
async def generate_scene_with_character(
    character_name: str,
    scene_description: str,
    camera: str = "medium close-up",
    expression: str = "neutral",
    provider: str = "kling",
    duration: int = 5,
    aspect_ratio: str = "9:16",
) -> VideoResult:
    """Create a video clip enforcing consistent facial features from a character profile."""
    from video_mcp.tools.character import generate_scene_with_character as _impl
    return await _impl(
        character_name=character_name,
        scene_description=scene_description,
        camera=camera,
        expression=expression,
        provider=provider,
        duration=duration,
        aspect_ratio=aspect_ratio,
    )

# 7. create_character_profile
@mcp.tool()
async def create_character_profile(
    reference_images: list[str],
    character_name: str,
    style: str = "pixar",
) -> CharacterProfile:
    """Register character styling prompts and references for facial lock consistency."""
    from video_mcp.tools.character import create_character_profile as _impl
    return await _impl(
        reference_images=reference_images,
        character_name=character_name,
        style=style,
    )

# 8. trim_clip
@mcp.tool()
async def trim_clip(
    input_path: str,
    start_time: float,
    duration: float | None = None,
    end_time: float | None = None,
    output_path: str | None = None,
) -> VideoResult:
    """Trim video timeline between start and duration specifications."""
    from video_mcp.tools.edit import trim_clip as _impl
    return await _impl(
        input_path=input_path,
        start_time=start_time,
        duration=duration,
        end_time=end_time,
        output_path=output_path,
    )

# 9. add_subtitles
@mcp.tool()
async def add_subtitles(
    video_path: str,
    srt_path: str,
    style: str = "bold_white",
    output_path: str | None = None,
) -> VideoResult:
    """Burn caption subtitles (.srt) directly into the video pixels (hardsub)."""
    from video_mcp.tools.edit import add_subtitles as _impl
    return await _impl(
        video_path=video_path,
        srt_path=srt_path,
        style=style,
        output_path=output_path,
    )

# 10. resize_to_platform
@mcp.tool()
async def resize_to_platform(
    input_path: str,
    platform: str = "instagram-reel",
    output_path: str | None = None,
) -> VideoResult:
    """Resize, center-crop, or pad a video container for Instagram, TikTok, or YouTube."""
    from video_mcp.tools.edit import resize_to_platform as _impl
    return await _impl(
        input_path=input_path,
        platform=platform,
        output_path=output_path,
    )

# 11. normalize_audio
@mcp.tool()
async def normalize_audio(
    input_path: str,
    target_lufs: float = -14.0,
    output_path: str | None = None,
) -> VideoResult:
    """Normalize video or audio loudness using loudnorm EBU standards (-14 LUFS)."""
    from video_mcp.tools.audio import normalize_audio as _impl
    return await _impl(
        input_path=input_path,
        target_lufs=target_lufs,
        output_path=output_path,
    )

# 12. video_quality_check
@mcp.tool()
async def video_quality_check(video_path: str) -> dict[str, Any]:
    """Validate video parameters against social upload recommendations (e.g. resolution, bitrate)."""
    from video_mcp.tools.analyze import video_quality_check as _impl
    return await _impl(video_path=video_path)

# 13. analyze_video
@mcp.tool()
async def analyze_video(video_path: str) -> AnalysisResult:
    """Detect scene cuts, estimate storyboard keyframes, and output visual analysis."""
    from video_mcp.tools.analyze import analyze_video as _impl
    return await _impl(video_path=video_path)

# 14. check_generation_job
@mcp.tool()
async def check_generation_job(job_id: str) -> JobStatus:
    """Get the current progress percent and state of a background job."""
    from video_mcp.tools.generate import check_generation_job as _impl
    return await _impl(job_id=job_id)

# 15. search_tools
@mcp.tool()
async def search_tools(query: str) -> dict[str, Any]:
    """Search for matching tools inside the video-mcp tool registry."""
    from video_mcp.tools.discovery import search_tools as _impl
    return await _impl(query=query)

def main() -> None:
    import os
    settings = get_settings()
    logger.info("mcp_server_starting", work_dir=str(settings.work_dir))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
    )

if __name__ == "__main__":
    main()
