# API and Tool Reference

This document provides technical schemas, input parameters, and return payloads for Video MCP's tools.

---

## 1. create_reel_from_brief (Flagship Orchestrator)

Generates a complete, vertical social media video from a plain narration script.

* **Schema Input**:
  ```json
  {
    "script": "string (narration dialog split by paragraph breaks)",
    "style": "string (default: 'pixar', allowed: 'pixar', 'cinematic')",
    "platform": "string (default: 'instagram', allowed: 'instagram', 'tiktok', 'youtube-shorts')",
    "provider": "string (default: 'kling')",
    "voice_id": "string (default: 'adam')",
    "character_name": "string (optional)",
    "output_path": "string (optional)"
  }
  ```
* **Response Payload** (`ReelResult`):
  ```json
  {
    "output_path": "/path/to/final_reel.mp4",
    "total_duration": 45.5,
    "scene_count": 5,
    "cost_breakdown": {
      "kling": 50.0,
      "elevenlabs": 455.0
    },
    "storyboard_path": "/path/to/storyboard_thumbnail.png"
  }
  ```

---

## 2. generate_video_from_image

Produces a short animated clip from an input image using Kling, Hailuo, or Veo.

* **Schema Input**:
  ```json
  {
    "image_path": "string (absolute path to PNG/JPG)",
    "motion_prompt": "string (directions like: zoom out, pan right)",
    "duration": "integer (default: 5, range: 1-60)",
    "aspect_ratio": "string (default: '9:16', allowed: '9:16', '16:9', '1:1')",
    "provider": "string (default: 'kling')",
    "model": "string (default: 'auto', allowed: 'auto', 'quality', 'fast')",
    "audio_prompt": "string (optional)"
  }
  ```
* **Response Payload** (`VideoResult`):
  ```json
  {
    "output_path": "/path/to/generated_clip.mp4",
    "duration_seconds": 5.0,
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "file_size_mb": 1.25,
    "provider_used": "kling",
    "cost_credits": 10.0
  }
  ```

---

## 3. generate_voiceover

Converts script paragraphs to voiceover files using ElevenLabs.

* **Schema Input**:
  ```json
  {
    "script": "string (narration text)",
    "voice_id": "string (default: 'adam')",
    "speed": "float (default: 0.95, range: 0.5 - 2.0)",
    "output_path": "string (optional)"
  }
  ```
* **Response Payload** (`AudioResult`):
  ```json
  {
    "output_path": "/path/to/voiceover.mp3",
    "duration_seconds": 12.35,
    "voice_id": "adam",
    "character_count": 145,
    "cost_credits": 145.0
  }
  ```

---

## 4. assemble_reel

Timeline concatenation and mixing.

* **Schema Input**:
  ```json
  {
    "clips": [
      {
        "clip_path": "/path/to/clip1.mp4",
        "start_time": 0.0,
        "duration": 5.0
      }
    ],
    "voiceover_path": "string (path to vo.mp3)",
    "bgm_path": "string (optional path to bgm.mp3)",
    "bgm_volume": "float (default: 0.12)",
    "output_path": "string (optional)",
    "aspect_ratio": "string (default: '9:16')",
    "add_captions": "boolean (default: true)"
  }
  ```
* **Response Payload** (`VideoResult`): Same as `VideoResult` schema.
