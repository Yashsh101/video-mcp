"""
Synchronous Python Client for video-mcp.

This client wraps the underlying async tool functions using asyncio.run
to expose a clean, synchronous interface for python scripts.

Example Usage:
    from video_mcp import Client
    client = Client()
    
    # Generate voiceover
    audio = client.generate_voiceover(script="Welcome to BreakoutAI!")
    print(f"Generated voiceover: {audio.output_path} ({audio.duration_seconds}s)")

    # Create character profile
    profile = client.create_character_profile(
        reference_images=["/path/to/bob.jpg"],
        character_name="Bob"
    )

    # Orchestrate full reel
    result = client.create_reel_from_brief(
        script="Bob was an entrepreneur. [SCENE] Bob starting his day.",
        character_name="Bob"
    )
    print(f"Completed Reel: {result.output_path}")
"""

import asyncio
from typing import Any

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


class Client:
    def __init__(self) -> None:
        pass

    def create_reel_from_brief(
        self,
        script: str,
        style: str = "pixar",
        platform: str = "instagram",
        provider: str = "kling",
        voice_id: str = "adam",
        character_name: str | None = None,
        output_path: str | None = None,
    ) -> ReelResult:
        from video_mcp.tools.generate import create_reel_from_brief
        return asyncio.run(
            create_reel_from_brief(
                script=script,
                style=style,
                platform=platform,
                provider=provider,
                voice_id=voice_id,
                character_name=character_name,
                output_path=output_path,
            )
        )

    def generate_video_from_image(
        self,
        image_path: str,
        motion_prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",
        provider: str = "kling",
        model: str = "auto",
        audio_prompt: str | None = None,
    ) -> VideoResult:
        from video_mcp.tools.generate import generate_video_from_image
        return asyncio.run(
            generate_video_from_image(
                image_path=image_path,
                motion_prompt=motion_prompt,
                duration=duration,
                aspect_ratio=aspect_ratio,
                provider=provider,
                model=model,
                audio_prompt=audio_prompt,
            )
        )

    def generate_voiceover(
        self,
        script: str,
        voice_id: str = "adam",
        speed: float = 0.95,
        output_path: str | None = None,
    ) -> AudioResult:
        from video_mcp.tools.generate import generate_voiceover
        return asyncio.run(
            generate_voiceover(
                script=script,
                voice_id=voice_id,
                speed=speed,
                output_path=output_path,
            )
        )

    def batch_generate_scenes(
        self,
        scenes: list[SceneRequest],
        provider: str = "kling",
        max_concurrent: int = 4,
    ) -> BatchResult:
        from video_mcp.tools.generate import batch_generate_scenes
        return asyncio.run(
            batch_generate_scenes(
                scenes=scenes,
                provider=provider,
                max_concurrent=max_concurrent,
            )
        )

    def assemble_reel(
        self,
        clips: list[ClipSequence],
        voiceover_path: str,
        bgm_path: str | None = None,
        bgm_volume: float = 0.12,
        output_path: str | None = None,
        aspect_ratio: str = "9:16",
        add_captions: bool = True,
    ) -> VideoResult:
        from video_mcp.tools.assemble import assemble_reel
        return asyncio.run(
            assemble_reel(
                clips=clips,
                voiceover_path=voiceover_path,
                bgm_path=bgm_path,
                bgm_volume=bgm_volume,
                output_path=output_path,
                aspect_ratio=aspect_ratio,
                add_captions=add_captions,
            )
        )

    def generate_scene_with_character(
        self,
        character_name: str,
        scene_description: str,
        camera: str = "medium close-up",
        expression: str = "neutral",
        provider: str = "kling",
        duration: int = 5,
        aspect_ratio: str = "9:16",
    ) -> VideoResult:
        from video_mcp.tools.character import generate_scene_with_character
        return asyncio.run(
            generate_scene_with_character(
                character_name=character_name,
                scene_description=scene_description,
                camera=camera,
                expression=expression,
                provider=provider,
                duration=duration,
                aspect_ratio=aspect_ratio,
            )
        )

    def create_character_profile(
        self,
        reference_images: list[str],
        character_name: str,
        style: str = "pixar",
    ) -> CharacterProfile:
        from video_mcp.tools.character import create_character_profile
        return asyncio.run(
            create_character_profile(
                reference_images=reference_images,
                character_name=character_name,
                style=style,
            )
        )

    def load_character_profile(self, character_name: str) -> CharacterProfile:
        from video_mcp.tools.character import load_character_profile
        return asyncio.run(load_character_profile(character_name=character_name))

    def trim_clip(
        self,
        input_path: str,
        start_time: float,
        duration: float | None = None,
        end_time: float | None = None,
        output_path: str | None = None,
    ) -> VideoResult:
        from video_mcp.tools.edit import trim_clip
        return asyncio.run(
            trim_clip(
                input_path=input_path,
                start_time=start_time,
                duration=duration,
                end_time=end_time,
                output_path=output_path,
            )
        )

    def add_subtitles(
        self,
        video_path: str,
        srt_path: str,
        style: str = "bold_white",
        output_path: str | None = None,
    ) -> VideoResult:
        from video_mcp.tools.edit import add_subtitles
        return asyncio.run(
            add_subtitles(
                video_path=video_path,
                srt_path=srt_path,
                style=style,
                output_path=output_path,
            )
        )

    def resize_to_platform(
        self,
        input_path: str,
        platform: str = "instagram-reel",
        output_path: str | None = None,
    ) -> VideoResult:
        from video_mcp.tools.edit import resize_to_platform
        return asyncio.run(
            resize_to_platform(
                input_path=input_path,
                platform=platform,
                output_path=output_path,
            )
        )

    def normalize_audio(
        self,
        input_path: str,
        target_lufs: float = -14.0,
        output_path: str | None = None,
    ) -> VideoResult:
        from video_mcp.tools.audio import normalize_audio
        return asyncio.run(
            normalize_audio(
                input_path=input_path,
                target_lufs=target_lufs,
                output_path=output_path,
            )
        )

    def video_quality_check(self, video_path: str) -> dict[str, Any]:
        from video_mcp.tools.analyze import video_quality_check
        return asyncio.run(video_quality_check(video_path=video_path))

    def analyze_video(self, video_path: str) -> AnalysisResult:
        from video_mcp.tools.analyze import analyze_video
        return asyncio.run(analyze_video(video_path=video_path))

    def check_generation_job(self, job_id: str) -> JobStatus:
        from video_mcp.tools.generate import check_generation_job
        return asyncio.run(check_generation_job(job_id=job_id))

    def search_tools(self, query: str) -> dict[str, Any]:
        from video_mcp.tools.discovery import search_tools
        return asyncio.run(search_tools(query=query))
