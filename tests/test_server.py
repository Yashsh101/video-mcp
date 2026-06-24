from pathlib import Path


def test_health_route_is_registered():
    server_source = Path("video_mcp/server.py").read_text(encoding="utf-8")
    assert '@mcp.custom_route("/health", methods=["GET"])' in server_source
    assert '{"status": "ok", "server": "video-mcp", "version": "0.1.0"}' in server_source
