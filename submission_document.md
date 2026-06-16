# AI-Powered Viral Reel Production Pipeline
**BreakoutAI — Round 2 Submission** · Yash Sharma · June 2026

---

## 1. Executive Summary

Built an end-to-end pipeline producing 4 Pixar-illustrated viral reels (9:16, ~60s) for entrepreneur Bob Campana, combining Gemini scene decomposition, GPT-4o image generation, Google Flow Veo 3.1 animation, ElevenLabs voiceover, and CapCut assembly. The key innovation is an **MCP server** ([Video-MCP](https://Video-MCP.fastmcp.app/mcp)) exposing 5 pipeline tools as endpoints, enabling any LLM agent to orchestrate video production autonomously. At scale, this reduces per-video production from **3 hours to 12 minutes at ~$0.40/video**.

---

## 2. Story Selection Rationale

| Video | Story | Viral Hook |
|-------|-------|------------|
| V1 | Restaurant Dishwasher → Steak | Rags-to-riches reversal — highest emotional contrast |
| V2 | 1990 Recession + Firewalk | Fear → triumph arc — universal founder resonance |
| V3 | Hot Tub + $50K Failure | Vulnerability + humor — drives shares and comments |
| V4 | NZ Billionaire | Aspiration + global scale — strong CTA energy |

Selection criteria: **emotional polarity** (contrast between low and high), **relatability** to founder audiences, and **visual richness** for Pixar-style illustration.

---

## 3. Visual Consistency Method

Bob's character (~70yr, silver-grey hair, rectangular glasses, Pixar *Up* style) was maintained via two complementary techniques:
- **ChatGPT same-chat persistence**: All scene images generated within a single GPT-4o session, preserving character memory across prompts.
- **Google Flow Character feature**: Uploaded Bob's reference image into Flow's character slot, anchoring facial features during Veo 3.1 animation.

---

## 4. Tools Used vs. Discovered

| Tool | Purpose | Why Chosen |
|------|---------|------------|
| Gemini 2.5 Flash | Scene breakdown → structured JSON | Superior instruction following for structured output |
| ChatGPT GPT-4o | Pixar-style image generation | Best character consistency via same-chat memory |
| Google Flow + Veo 3.1 | Image-to-video animation | Highest quality motion; character anchoring |
| **VEO Automation Extension** | **Batch Flow automation** | **Key discovery — eliminates manual queue management** |
| ElevenLabs | Voiceover generation | Most natural prosody; API-ready |
| CapCut Web | Final assembly + captions | Fast timeline editing; auto-captions |
| FastMCP Horizon | MCP server deployment | Zero-infra serverless MCP hosting |
| Higgsfield Soul ID | Character consistency R&D | Explored for face-lock; reserved for v2 |

---

## 5. Workflow Executed

```
Story Text → [Gemini] Scene Breakdown (7 scenes/video)
         → [GPT-4o] Pixar Image Generation (same-chat)
         → [Google Flow + VEO Automation] Animation (batch)
         → [ElevenLabs] Voiceover MP3
         → [CapCut] Stitch + Captions + Export 9:16
```

---

## 6. What Failed + How Adapted

| Failure | Adaptation |
|---------|------------|
| n8n Veo node — API not publicly available | Switched to manual Google Flow + VEO Automation extension |
| Nano Banana face drift across scenes | Moved to ChatGPT same-chat method for consistency |
| VEO Automation prompt-length errors | Shortened motion prompts to <100 words |

---

## 7. Proposed Agentic Pipeline (n8n Architecture)

```
Input Story Text
  → Gemini API: scene_breakdown JSON (7 scenes)
  → DALL·E 3 API: parallel image generation (7 images)
  → Veo API (when public): parallel animation (7 clips)
  → ElevenLabs API: voiceover MP3
  → FFmpeg: stitch clips + merge audio
  → Google Drive API: upload + organize
  → Gmail API: notify client with delivery link
```

| Metric | Manual | Automated |
|--------|--------|-----------|
| Time per video | ~3 hours | ~12 minutes |
| Cost per video | — | ~$0.40 |
| Monthly throughput | ~15 videos | **100+ videos** |

---

## 8. MCP Server Architecture

**Deployed**: [https://Video-MCP.fastmcp.app/mcp](https://Video-MCP.fastmcp.app/mcp)
**GitHub**: [github.com/Yashsh101/video-mcp](https://github.com/Yashsh101/video-mcp)

5 exposed tools: `generate_scene_breakdown`, `generate_scene_image_prompt`, `generate_motion_prompt`, `generate_voiceover`, `get_workflow_status`. Any MCP-compatible LLM agent (Claude, Gemini) can call these endpoints to orchestrate full video production without human intervention.

---

## 9. Scalability for Bulk Production

The pipeline is **author-agnostic**: swap the input story corpus and character reference, and the same workflow produces branded reels for any personal brand. Character consistency scales via Soul ID face-lock (v2). The n8n pipeline + MCP server together form a **repeatable content factory** — one operator, unlimited authors.

---

## 10. Suggested Improvements

| Improvement | Impact |
|-------------|--------|
| Replace ChatGPT with **Higgsfield Soul ID** | Pixel-perfect face lock across all scenes |
| Add **Creatomate API** | Eliminate manual CapCut assembly |
| **CLIP embedding scoring** | Automated visual quality gate before export |
| **Seedance 2.0** as Veo alternative | No watermark; comparable motion quality |

---

> *Built to demonstrate that AI video production is no longer a creative bottleneck — it's an engineering problem with a scalable solution.*
