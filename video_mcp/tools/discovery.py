from typing import Any

# Central registry of tool metadata for discovery
TOOLS_METADATA = [
    {
        "name": "create_reel_from_brief",
        "description": "Orchestrates full production from script brief to a captioned vertical reel.",
    },
    {
        "name": "generate_video_from_image",
        "description": "Creates a short motion video from a reference image using Kling, Hailuo, or Veo.",
    },
    {
        "name": "generate_video_from_text",
        "description": "Generates a video directly from a descriptive text prompt.",
    },
    {
        "name": "batch_generate_scenes",
        "description": "Processes multiple scene generation requests concurrently.",
    },
    {
        "name": "generate_voiceover",
        "description": "Generates spoken voiceover MP3 using ElevenLabs TTS.",
    },
    {
        "name": "check_generation_job",
        "description": "Checks the current execution status of background video jobs.",
    },
    {
        "name": "assemble_reel",
        "description": "Concatenates individual scenes, mixes voiceover and background music, and burns captions.",
    },
    {
        "name": "trim_clip",
        "description": "Trims a video clip between a start time and duration/end time.",
    },
    {
        "name": "add_audio_to_video",
        "description": "Mixes or replaces the audio track of a video with an external audio file.",
    },
    {
        "name": "add_subtitles",
        "description": "Burns SubRip (SRT) subtitles directly into the video pixels (hardsub).",
    },
    {
        "name": "resize_to_platform",
        "description": "Resizes, crops, or pads video for platforms like Instagram Reels, TikTok, and YouTube.",
    },
    {
        "name": "create_character_profile",
        "description": "Saves reference images and styling prompts to enforce face consistency.",
    },
    {
        "name": "load_character_profile",
        "description": "Loads a saved character profile by name.",
    },
    {
        "name": "generate_scene_with_character",
        "description": "Generates a scene using a reference image and character descriptor to lock face features.",
    },
    {
        "name": "normalize_audio",
        "description": "Normalizes video or audio file track loudness to streaming standards (-14 LUFS).",
    },
    {
        "name": "extract_audio",
        "description": "Extracts the audio channel from a video file into MP3 or WAV format.",
    },
    {
        "name": "mix_audio_tracks",
        "description": "Blends multiple audio files with custom volumes and start offsets.",
    },
    {
        "name": "analyze_video",
        "description": "Detects scene cuts, extracts storyboards, and rates technical video specs.",
    },
    {
        "name": "video_quality_check",
        "description": "Validates resolution, bitrate, audio presence, and duration against reel standards.",
    },
    {
        "name": "search_tools",
        "description": "Finds specific tools and features in the video-mcp tool suite by keywords.",
    }
]

async def search_tools(query: str) -> dict[str, Any]:
    """
    Search the registered tools in video-mcp.

    Inputs:
        query: Search keywords or phrases.

    Returns:
        Dict detailing matched tools and relevance scores.
    """
    q = query.lower().strip()
    matches: list[dict[str, Any]] = []

    for tool in TOOLS_METADATA:
        name = tool["name"]
        desc = tool["description"]
        
        score = 0.0
        if q in name.lower():
            score += 1.0
        if q in desc.lower():
            score += 0.5

        if score > 0.0:
            matches.append({
                "name": name,
                "description": desc,
                "match_score": score,
            })

    # Sort matches by descending score
    matches.sort(key=lambda x: x["match_score"], reverse=True)

    return {"tools": matches}
