import ast
from pathlib import Path


def test_main_uses_streamable_http_transport():
    source = Path("video_mcp/server.py").read_text(encoding="utf-8")
    module = ast.parse(source)

    main_def = next(
        node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    run_call = next(
        node
        for node in ast.walk(main_def)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mcp"
        and node.func.attr == "run"
    )
    kw = {item.arg: item.value for item in run_call.keywords}

    assert kw["transport"].value == "streamable-http"
    assert kw["host"].value == "0.0.0.0"
    assert isinstance(kw["port"], ast.Call)
