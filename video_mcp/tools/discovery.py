from __future__ import annotations
import re
from typing import Any

# Authoritative tool registry — exact match with @mcp.tool() in server.py
# Do NOT add tools here that don't exist in server.py
TOOLS_REGISTRY: list[dict[str, Any]] = [
    {
        "name": "create_reel_from_brief",
        "description": "Orchestrates full production from script brief to a captioned vertical reel.",
        "category": "orchestration",
        "tags": ["reel", "script", "generate", "full-pipeline", "flagship", "brief"],
    },
    {
        "name": "generate_video_from_image",
        "description": "Creates a short motion video from a reference image using Kling, Hailuo, or Veo.",
        "category": "generation",
        "tags": ["video", "image", "kling", "hailuo", "veo", "generate", "motion"],
    },
    {
        "name": "generate_voiceover",
        "description": "Generates spoken voiceover MP3 using ElevenLabs TTS.",
        "category": "audio",
        "tags": ["audio", "voiceover", "elevenlabs", "tts", "speech", "voice"],
    },
    {
        "name": "batch_generate_scenes",
        "description": "Processes multiple scene generation requests concurrently.",
        "category": "generation",
        "tags": ["batch", "scenes", "concurrent", "generate", "parallel", "multiple"],
    },
    {
        "name": "assemble_reel",
        "description": "Concatenates individual scenes, mixes voiceover and background music, and burns captions.",
        "category": "assembly",
        "tags": ["assemble", "concat", "captions", "audio", "reel", "mix", "music"],
    },
    {
        "name": "generate_scene_with_character",
        "description": "Generates a scene using a reference image and character descriptor to lock face features.",
        "category": "character",
        "tags": ["character", "face", "consistency", "scene", "generate", "lock"],
    },
    {
        "name": "create_character_profile",
        "description": "Saves reference images and styling prompts to enforce face consistency.",
        "category": "character",
        "tags": ["character", "profile", "reference", "face", "style", "create"],
    },
    {
        "name": "trim_clip",
        "description": "Trims a video clip between a start time and duration/end time.",
        "category": "editing",
        "tags": ["trim", "cut", "clip", "edit", "duration", "start", "end"],
    },
    {
        "name": "add_subtitles",
        "description": "Burns SubRip (SRT) subtitles directly into the video pixels (hardsub).",
        "category": "editing",
        "tags": ["subtitles", "captions", "srt", "hardsub", "text", "burn"],
    },
    {
        "name": "resize_to_platform",
        "description": "Resizes, crops, or pads video for platforms like Instagram Reels, TikTok, and YouTube.",
        "category": "editing",
        "tags": ["resize", "crop", "instagram", "tiktok", "youtube", "platform", "format"],
    },
    {
        "name": "normalize_audio",
        "description": "Normalizes video or audio file track loudness to streaming standards (-14 LUFS).",
        "category": "audio",
        "tags": ["audio", "normalize", "lufs", "loudness", "streaming", "volume"],
    },
    {
        "name": "video_quality_check",
        "description": "Validates resolution, bitrate, audio presence, and duration against reel standards.",
        "category": "analysis",
        "tags": ["quality", "validate", "resolution", "bitrate", "check", "inspect"],
    },
    {
        "name": "analyze_video",
        "description": "Detects scene cuts, extracts storyboards, and rates technical video specs.",
        "category": "analysis",
        "tags": ["analyze", "scene", "storyboard", "keyframes", "inspect", "detect"],
    },
    {
        "name": "check_generation_job",
        "description": "Checks the current execution status of a background video generation job.",
        "category": "jobs",
        "tags": ["job", "status", "progress", "async", "poll", "check"],
    },
    {
        "name": "search_tools",
        "description": "Finds specific tools and features in the video-mcp tool suite by keywords.",
        "category": "discovery",
        "tags": ["search", "find", "tools", "discovery", "help", "list"],
    },
]


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase tokens for multi-word matching."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


async def search_tools(query: str) -> dict[str, Any]:
    """
    Search the registered tools in video-mcp using multi-token scoring.

    Inputs:
        query: Search keywords or phrases (e.g. "video generation", "audio normalize")

    Returns:
        Dict with matched tools sorted by relevance score, plus total count.
    """
    q = query.lower().strip()
    q_tokens = _tokenize(q)
    matches: list[dict[str, Any]] = []

    for tool in TOOLS_REGISTRY:
        name_tokens = _tokenize(tool["name"])
        desc_tokens = _tokenize(tool["description"])
        tag_tokens: set[str] = set()
        for tag in tool.get("tags", []):
            tag_tokens.update(_tokenize(tag))

        score = 0.0

        # Exact full-string substring match (highest weight)
        if q in tool["name"].lower():
            score += 3.0
        if q in tool["description"].lower():
            score += 1.5

        # Token overlap scoring
        name_overlap = len(q_tokens & name_tokens)
        desc_overlap = len(q_tokens & desc_tokens)
        tag_overlap = len(q_tokens & tag_tokens)

        score += name_overlap * 2.0
        score += desc_overlap * 0.8
        score += tag_overlap * 1.2

        # Exact category match
        if q == tool.get("category", ""):
            score += 2.0

        if score > 0.0:
            matches.append({
                "name": tool["name"],
                "description": tool["description"],
                "category": tool["category"],
                "match_score": round(score, 2),
            })

    matches.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "query": query,
        "total_matches": len(matches),
        "tools": matches,
        "hint": (
            "Use the tool name directly to call it. "
            "Start with create_reel_from_brief for end-to-end reel generation."
        ),
    }
