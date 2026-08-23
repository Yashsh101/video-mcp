# Repository Audit: video-mcp

**Audit date:** 2026-08-23
**Repository path:** `/workspace/video-mcp`
**Branch state at audit:** cloned default branch; no main-branch push performed.

## Score

**BROKEN**

## Evidence

| Check | Result |
|---|---|
| README.md | present |
| requirements.txt | not present |
| package.json | not present |
| Existing test command | `python3 -m pytest -q` |
| Test result | **FAIL** — count unavailable |
| Dockerfile | present |
| CI/CD workflows | .github/workflows/ci.yml, .github/workflows/publish.yml |
| Type hints | detected |
| FastAPI detected | no |
| Pydantic models/imports | detected |
| `.env.example` | present |
| Possible hardcoded secrets | none matched audit pattern |
| API error handling | not applicable |

## Findings

- Existing test command fail: count unavailable.

## Test output

```text

==================================== ERRORS ====================================
___________________ ERROR collecting tests/test_assemble.py ____________________
ImportError while importing test module '/workspace/video-mcp/tests/test_assemble.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_assemble.py:5: in <module>
    from video_mcp.tools.edit import trim_clip, add_subtitles, resize_to_platform
video_mcp/tools/__init__.py:1: in <module>
    from video_mcp.tools.analyze import (
video_mcp/tools/analyze.py:4: in <module>
    import structlog
E   ModuleNotFoundError: No module named 'structlog'
_____________________ ERROR collecting tests/test_cache.py _____________________
ImportError while importing test module '/workspace/video-mcp/tests/test_cache.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_cache.py:6: in <module>
    from video_mcp.tools.generate import generate_video_from_image, generate_voiceover
video_mcp/tools/__init__.py:1: in <module>
    from video_mcp.tools.analyze import (
video_mcp/tools/analyze.py:4: in <module>
    import structlog
E   ModuleNotFoundError: No module named 'structlog'
___________________ ERROR collecting tests/test_generate.py ____________________
ImportError while importing test module '/workspace/video-mcp/tests/test_generate.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_generate.py:7: in <module>
    from video_mcp.tools.generate import (
video_mcp/tools/__init__.py:1: in <module>
    from video_mcp.tools.analyze import (
video_mcp/tools/analyze.py:4: in <module>
    import structlog
E   ModuleNotFoundError: No module named 'structlog'
___________________ ERROR collecting tests/test_security.py ____________________
ImportError while importing test module '/workspace/video-mcp/tests/test_security.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.12/importlib/__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_security.py:6: in <module>
    from video_mcp.tools.edit import trim_clip
video_mcp/tools/__init__.py:1: in <module>
    from video_mcp.tools.analyze import (
video_mcp/tools/analyze.py:4: in <module>
    import structlog
E   ModuleNotFoundError: No module named 'structlog'
=========================== short test summary info ============================
ERROR tests/test_assemble.py
ERROR tests/test_cache.py
ERROR tests/test_generate.py
ERROR tests/test_security.py
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!

```

## Fix decision

This audit is evidence for the next phase. Fixes must remain narrow, preserve architecture, never touch `.env` files, and must be verified before any branch push. If an issue requires an architectural decision, the repository must be skipped and recorded in `MASTER_LOG.md`.

## Disposition

Skipped: protocol-level health, provider credentials, FFmpeg availability, and runtime hosting require an integration decision beyond a narrow repository fix.

No `.env` file was touched, no tests were deleted, and no main branch was modified.
