from __future__ import annotations
import json
import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP("video-mcp")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
VOICE_IDS = {
    "Adam":   "pNInz6obpgDQGcFmaJgB",
    "Antoni": "ErXwobaYiN019PkySvjV",
}

@mcp.tool
def health_check() -> str:
    """Verify server is reachable."""
    return "video-mcp ok"

@mcp.tool
async def generate_scene_breakdown(story_text: str, num_scenes: int = 7) -> str:
    """Break entrepreneur story into N scenes using Perplexity."""
    if not PERPLEXITY_API_KEY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not set"})
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": f"""Break this story into {num_scenes} scenes for a 60s reel.
Story: {story_text}
Return ONLY a JSON array. Each element: scene_num, visual_description, voiceover_line, motion_prompt, duration_seconds."""}],
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

@mcp.tool
def generate_scene_image_prompt(scene_description: str, scene_num: int) -> str:
    """Generate optimized ChatGPT image prompt for a scene."""
    return f"""Pixar 'Up' movie illustration style. 3D animated, NOT photorealistic.
Elderly male entrepreneur, ~70 years old, silver-grey hair, rectangular black glasses.
Scene {scene_num}: {scene_description}
9:16 vertical composition. Warm cinematic colors. No text, no watermarks.
Maintain consistent character face across all scenes."""

@mcp.tool
def generate_motion_prompt(scene_description: str, scene_emotion: str = "neutral") -> str:
    """Generate Google Flow motion prompt for animating a still image."""
    cameras = {
        "happy":      "Slow pull back. Warm golden light.",
        "sad":        "Extremely slow push in. Single dim lamp.",
        "tense":      "Static shot. Dramatic shadows. Handheld energy.",
        "triumphant": "Slow pull back. Warm light. Triumphant energy.",
        "neutral":    "Slow cinematic push in toward subject.",
    }
    camera = cameras.get(scene_emotion, cameras["neutral"])
    return f"""{camera}
Pixar illustrated style. 9:16 vertical.
Subtle natural movement: breathing, gentle breeze, particles.
No camera shake. No facial distortion.
Scene: {scene_description}"""

@mcp.tool
async def generate_voiceover(script: str, video_id: str, voice: str = "Adam") -> str:
    """Generate voiceover MP3 via ElevenLabs free tier."""
    if not ELEVENLABS_API_KEY:
        return json.dumps({"error": "ELEVENLABS_API_KEY not set"})
    voice_id = VOICE_IDS.get(voice, VOICE_IDS["Adam"])
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={"text": script, "model_id": "eleven_monolingual_v1",
                  "voice_settings": {"stability": 0.65, "similarity_boost": 0.75}},
            timeout=30,
        )
        resp.raise_for_status()
        return json.dumps({"status": "success", "video_id": video_id,
                           "chars_used": len(script)})

@mcp.tool
def get_workflow_status(video_id: str) -> str:
    """Return pipeline checklist for a video_id."""
    return json.dumps({
        "video_id": video_id,
        "steps": [
            {"step": 1, "tool": "generate_scene_breakdown"},
            {"step": 2, "tool": "generate_scene_image_prompt x7"},
            {"step": 3, "tool": "ChatGPT GPT-4o (manual)"},
            {"step": 4, "tool": "generate_motion_prompt x7"},
            {"step": 5, "tool": "Google Flow (manual)"},
            {"step": 6, "tool": "generate_voiceover"},
            {"step": 7, "tool": "CapCut assembly (manual)"},
        ]
    })

if __name__ == "__main__":
    mcp.run()
else:
    app = mcp.http_app(path="/mcp")