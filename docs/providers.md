# Providers and Integrations

Video MCP integrates with multiple generative audio and video engines. This guide details configuration parameters, authentication keys, and fallback behaviors.

---

## 🔑 Authentication Settings

Configure credentials in your environment or Claude Desktop environment blocks:

| Environment Variable | Description | Cost / Rates |
| :--- | :--- | :--- |
| `KLING_API_KEY` | Secret token to authenticate Kling AI. | 10 credits / 5s generation. |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS secret token. | 1 character / credit. |
| `HAILUO_API_KEY` | Hailuo AI provider key. | 15 credits / 5s generation. |
| `VEO_API_KEY` | Google Veo API key. | 30 credits / generation. |
| `VIDEO_MCP_WORK_DIR` | Location where output clips are compiled (Default: `/tmp/video-mcp`). | N/A |

---

## 🤖 Supported Providers

### 1. Kling AI (Image-to-Video, Text-to-Video)
Kling is the default provider for high-fidelity scene generation:
* **Image-to-Video**: Animates character inputs or scenes with a motion prompt.
* **Text-to-Video**: Direct synthesis of descriptive visual scripts.
* **Key Configuration**: Exposes a `model` parameter (`auto`, `quality`, or `fast`). `quality` is recommended for final production compiles, and `fast` for testing.

### 2. ElevenLabs (High-Fidelity Audio)
Synthesizes dialogues to voiceover tracks:
* **Voices**: Pre-configured voices like `adam`, `antoni`, `bella`, `rachel`, or custom cloned IDs.
* **Speed control**: Supports modifications between `0.5` and `2.0` (default `0.95` to keep pacing conversational).

### 3. Hailuo (MiniMax Video Generation)
An alternative engine for image-to-video animation:
* Known for detailed physics simulations.
* Automatically fallback target if Kling rate limits or credits are exhausted.

### 4. Google Veo
Integrated stub configuration for ultra-high-resolution widescreen or vertical cinematic animations.

---

## 🔄 Resilience & Provider Fallback Rules

If generative calls fail during a compilation run, the server follows this fallback hierarchy:

```
[Kling Quality] -> Timeout/Limit -> [Kling Fast] -> Limit -> [Hailuo Video] -> Fail -> [Black Placeholder]
```

1. **Model Fallback**: If Kling `quality` fails due to quota limits, it retries automatically using model `fast` or `auto`.
2. **Provider Fallback**: If Kling returns `QUOTA_EXCEEDED` or rate limits persist, the task is forwarded to Hailuo or Veo.
3. **Asset Fallback**: If clip generation fails entirely, the system generates a black blank placeholder clip via FFmpeg (`make_placeholder_clip`) of the exact scene duration. This prevents compiler crashes and guarantees a complete final `.mp4` reel output.
