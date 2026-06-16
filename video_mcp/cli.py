import shutil
import sys

import click

from video_mcp.client import Client
from video_mcp.config import get_settings
from video_mcp.errors import MCPVideoError


def _safe_echo(message: str, err: bool = False) -> None:
    """Echo a message with emoji, fallback to standard ASCII characters if encoding fails."""
    try:
        message.encode(sys.stdout.encoding or "ascii")
        click.echo(message, err=err)
    except UnicodeEncodeError:
        # Simple replacements of common emojis used in CLI
        ascii_msg = (
            message.replace("✅", "[PASS]")
            .replace("❌", "[FAIL]")
            .replace("🎉", "[SUCCESS]")
            .replace("⚠️", "[WARN]")
        )
        click.echo(ascii_msg, err=err)

def _print_status(label: str, passed: bool, info: str = "") -> None:
    symbol = "✅" if passed else "❌"
    _safe_echo(f"{symbol} {label}: {info}")

@click.group()
def main() -> None:
    """video-mcp CLI: Orchestrate AI video generation from the command line."""
    pass

@main.command()
def doctor() -> None:
    """Diagnose local configurations, environment keys, and FFmpeg capability."""
    click.echo("Running diagnostics for video-mcp...")
    
    # 1. Python Version Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_pass = sys.version_info >= (3, 11)
    _print_status("Python 3.11+", py_pass, f"Detected Python {py_ver}")

    # 2. FFmpeg / FFprobe check
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    ffmpeg_pass = ffmpeg_path is not None and ffprobe_path is not None
    ffmpeg_info = f"ffmpeg found at {ffmpeg_path}" if ffmpeg_pass else "ffmpeg or ffprobe missing on PATH"
    _print_status("FFmpeg Dependency", ffmpeg_pass, ffmpeg_info)

    # 3. WORK_DIR writable check
    settings = get_settings()
    work_dir = settings.work_dir
    write_pass = False
    try:
        test_file = work_dir / ".doctor_write_test"
        test_file.write_text("write_test", encoding="utf-8")
        test_file.unlink()
        write_pass = True
        write_info = f"Writable at {work_dir}"
    except Exception as e:
        write_info = f"Failed writing to {work_dir}: {e}"
    _print_status("Work Directory", write_pass, write_info)

    # 4. API Key Verification
    keys = {
        "KLING_API_KEY": settings.kling_api_key,
        "ELEVENLABS_API_KEY": settings.elevenlabs_api_key,
        "HAILUO_API_KEY": settings.hailuo_api_key,
        "VEO_API_KEY": settings.veo_api_key,
    }
    for k, val in keys.items():
        key_pass = val is not None
        key_info = f"Masked: {val[:4]}...{val[-4:]}" if val is not None else "Not configured"
        _print_status(k, key_pass, key_info)

    # Critical failures check
    if not (py_pass and ffmpeg_pass and write_pass):
        _safe_echo("\n❌ Diagnostics failed. Please resolve the critical errors above.", err=True)
        sys.exit(1)
        
    _safe_echo("\n🎉 Diagnostics passed! video-mcp is ready for production.")

@main.command()
@click.option("--image", required=True, help="Path to input image file.")
@click.option("--prompt", required=True, help="Motion direction instructions.")
@click.option("--duration", default=5, type=int, help="Length in seconds (default: 5).")
@click.option("--provider", default="kling", help="AI generator (default: kling).")
@click.option("--output", help="Optional output path destination.")
def generate(image: str, prompt: str, duration: int, provider: str, output: str | None) -> None:
    """Generate a short video clip from an input image reference."""
    client = Client()
    click.echo(f"Submitting image-to-video request to {provider}...")
    try:
        with click.progressbar(length=100, label="Generating Video") as bar:
            # Run clip generation
            res = client.generate_video_from_image(
                image_path=image,
                motion_prompt=prompt,
                duration=duration,
                provider=provider,
            )
            if output:
                import shutil
                shutil.copy(res.output_path, output)
                res.output_path = output
            bar.update(100)
        _safe_echo("✅ Video created successfully!")
        click.echo(f"Output Path: {res.output_path}")
        click.echo(f"Duration: {res.duration_seconds}s | Size: {res.file_size_mb}MB")
    except MCPVideoError as e:
        _safe_echo(f"❌ Generation error: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option("--script", required=True, help="Text dialogue narration script.")
@click.option("--voice", default="adam", help="ElevenLabs voice ID (default: adam).")
@click.option("--output", help="Optional destination path.")
def voiceover(script: str, voice: str, output: str | None) -> None:
    """Synthesize narration script to spoken audio file."""
    client = Client()
    click.echo(f"Synthesizing voiceover with voice '{voice}'...")
    try:
        res = client.generate_voiceover(script=script, voice_id=voice, output_path=output)
        _safe_echo("✅ Voiceover created successfully!")
        click.echo(f"Output Path: {res.output_path}")
        click.echo(f"Duration: {res.duration_seconds:.2f}s | Chars: {res.character_count}")
    except MCPVideoError as e:
        _safe_echo(f"❌ Voiceover error: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option("--script", required=True, help="Full narration script containing scenes.")
@click.option("--style", default="pixar", help="Visual style theme (default: pixar).")
@click.option("--platform", default="instagram", help="Branded dimensions (instagram, youtube).")
@click.option("--character", help="Saved character profile name.")
@click.option("--output", help="Optional final MP4 destination.")
def reel(script: str, style: str, platform: str, character: str | None, output: str | None) -> None:
    """Orchestrate full production pipeline to compile an animated vertical reel."""
    client = Client()
    click.echo("Orchestrating complete script-to-reel pipeline...")
    try:
        res = client.create_reel_from_brief(
            script=script,
            style=style,
            platform=platform,
            character_name=character,
            output_path=output,
        )
        _safe_echo("\n🎉 Video Reel compiled successfully!")
        click.echo(f"Final Output: {res.output_path}")
        click.echo(f"Reel Duration: {res.total_duration:.1f}s | Scenes: {res.scene_count}")
        click.echo("Cost Breakdown:")
        for provider, cost in res.cost_breakdown.items():
            click.echo(f" - {provider}: {cost:.1f} credits")
        if res.storyboard_path:
            click.echo(f"Storyboard Thumbnail: {res.storyboard_path}")
    except MCPVideoError as e:
        _safe_echo(f"❌ Orchestration error: {e}", err=True)
        sys.exit(1)

@main.command()
@click.argument("path")
def info(path: str) -> None:
    """Analyze video track composition and technical metrics."""
    client = Client()
    click.echo(f"Analyzing {path}...")
    try:
        res = client.analyze_video(video_path=path)
        click.echo("\nAnalysis Results:")
        click.echo(f"Quality Score: {res.quality_score:.1f}/100.0")
        click.echo(f"Detected Scenes: {len(res.scenes)}")
        if res.issues:
            click.echo("Issues Found:")
            for issue in res.issues:
                _safe_echo(f" - ⚠️ {issue}")
        else:
            _safe_echo(" - ✅ No quality issues found!")
        if res.thumbnails:
            click.echo("Keyframe Thumbnails:")
            for thumb in res.thumbnails:
                click.echo(f" - {thumb}")
    except MCPVideoError as e:
        _safe_echo(f"❌ Analysis error: {e}", err=True)
        sys.exit(1)

@main.command()
def providers() -> None:
    """List available AI providers and their status configurations."""
    settings = get_settings()
    click.echo("Known AI video/audio generation providers:")
    
    provs = [
        {"name": "kling", "env": "KLING_API_KEY", "cost": "10-20 credits/clip", "configured": settings.kling_api_key is not None},
        {"name": "elevenlabs", "env": "ELEVENLABS_API_KEY", "cost": "1 credit/character", "configured": settings.elevenlabs_api_key is not None},
        {"name": "hailuo", "env": "HAILUO_API_KEY", "cost": "15 credits/clip", "configured": settings.hailuo_api_key is not None},
        {"name": "veo", "env": "VEO_API_KEY", "cost": "30 credits/clip", "configured": settings.veo_api_key is not None},
    ]

    for p in provs:
        status = "Configured" if p["configured"] else "Not Configured"
        name_str = str(p["name"])
        click.echo(f"\n- Provider: {name_str.upper()}")
        click.echo(f"  Env Var:  {str(p['env'])}")
        click.echo(f"  Status:   {status}")
        click.echo(f"  Est Cost: {str(p['cost'])}")

if __name__ == "__main__":
    main()
