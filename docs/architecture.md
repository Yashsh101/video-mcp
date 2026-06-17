# System Architecture

This guide details the technical layers, data models, and workflow sequences within the Video MCP Server.

---

## 🏗️ Technical Layers

Video MCP is structured into four layers, enforcing separation of concerns:

```
                  ┌──────────────────────────────┐
                  │          FastMCP             │
                  │   Exposes Tools & Resources  │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │      Guardrail Checks        │
                  │   Validates Paths & Size     │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │    Caching & Hashing Layer   │
                  │  Checks and saves payloads   │
                  └──────────────┬───────────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
      ┌─────────────────────────┐ ┌─────────────────────────┐
      │     API Providers       │ │     Local Assembly      │
      │  (Kling / ElevenLabs)   │ │  (FFmpeg timeline/srt)  │
      └─────────────────────────┘ └─────────────────────────┘
```

1.  **Transport/Interface Layer (`server.py`, `cli.py`)**: Defines FastMCP server mappings and CLI commands. Handlers invoke lazy-loaded functions.
2.  **Safety Layer (`guardrails.py`)**: Runs pre-execution checks on aspect ratio, size limits, and sanitizes prompts. Enforces strict boundary verification to block path traversal outside `WORK_DIR`.
3.  **Caching Layer (`cache.py`)**: Computes SHA-256 hashes of input payloads and copies files to and from `.mcp_cache/`.
4.  **Adapter/Execution Layer (`providers/`, `tools/`)**: Implements client abstractions for Kling, ElevenLabs, and subprocess configurations for FFmpeg.

---

## 🔄 Execution Sequences

### 1. Script-to-Reel Compilation Workflow
The flagship orchestrator `create_reel_from_brief` coordinates voice synthesis and parallel scene generation:

```mermaid
sequenceDiagram
    participant C as MCP Client (LLM)
    participant O as Orchestrator Tool
    participant CA as Cache Layer
    participant AP as API Providers (GenAI)
    participant FF as FFmpeg Engine

    C->>O: Call create_reel_from_brief(script, style, voice)
    O->>CA: Get cached voiceover(script, voice)
    alt Cache Hit
        CA-->>O: Return cached vo.mp3
    else Cache Miss
        O->>AP: Synthesize TTS via ElevenLabs
        AP-->>O: Return vo.mp3
        O->>CA: Cache voiceover file
    end
    
    Note over O: Split script into scenes & calculate scene durations
    
    par Scene Generation (1 to N)
        O->>CA: Get cached video(prompt, style)
        alt Cache Hit
            CA-->>O: Return cached scene.mp4
        else Cache Miss
            O->>AP: Generate scene clip via Kling/Veo
            AP-->>O: Return scene.mp4
            O->>CA: Cache video file
        end
    end

    O->>FF: Stitch clips, mix audio tracks, burn-in captions
    FF-->>O: Return final compiled_reel.mp4
    O-->>C: Return ReelResult
```

### 2. Guardrails Boundary Checks
To prevent path traversal, all input/output paths are resolved against `WORK_DIR`:

```python
# Simplified flow inside guardrails.py
def validate_input_path(path_str: str) -> Path:
    work_dir = settings.work_dir.resolve()
    path = Path(path_str).resolve()
    
    # Check traversal boundary
    try:
        path.relative_to(work_dir)
    except ValueError:
        raise PathViolationError("Escape attempt blocked")
    
    if not path.exists():
        raise FileNotFoundError()
    return path
```
