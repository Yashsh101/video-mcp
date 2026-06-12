# ─── submit_job.py — CLI script to fire jobs ───────────────────────────────────
import os
import sys
from fastmcp import FastMCP  # if not already

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

base = os.path.dirname(os.path.abspath(__file__))

mcp = FastMCP("video-mcp")
submit_py = '''#!/usr/bin/env python3
"""
CLI: Submit a video generation job to the connector.
Usage:
    python submit_job.py payloads/v1_dishwasher_steak.json
    python submit_job.py payloads/v2_firewalk.json --stream
"""

import argparse, json, sys, time
import httpx

API_BASE = "http://localhost:8000"


def submit(payload_path: str, stream: bool = False):
    with open(payload_path) as f:
        payload = json.load(f)

    resp = httpx.post(f"{API_BASE}/api/generate", json=payload, timeout=30)
    resp.raise_for_status()
    job = resp.json()
    print(f"\\n✅ Job submitted: {job[\'job_id\']} | Video: {job[\'video_id\']}")
    print(f"   {job[\'message\']}\\n")

    if stream:
        print("📡 Streaming pipeline progress via SSE...")
        with httpx.stream("GET", f"{API_BASE}/api/stream/{job[\'job_id\']}") as r:
            for line in r.iter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if data.get("done"):
                        print(f"\\n🏁 Pipeline {data[\'status\'].upper()}")
                        break
                    print(f"   [{data.get(\'progress\', 0):3d}%] {data.get(\'step\', '')}")
    else:
        print("📊 Poll with:")
        print(f"   curl http://localhost:8000/api/status/{job[\'job_id\']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", help="Path to payload JSON file")
    parser.add_argument("--stream", action="store_true", help="Stream SSE progress")
    args = parser.parse_args()
    submit(args.payload, args.stream)
'''

with open(os.path.join(base, "submit_job.py"), "w") as f:
    f.write(submit_py)

# ─── Dockerfile ────────────────────────────────────────────────────────────────
dockerfile = '''# Stage 1: builder
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
# Install Playwright + Chromium
RUN pip install playwright && playwright install chromium && playwright install-deps chromium
COPY . .
RUN mkdir -p output assets refs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

with open(os.path.join(base, "Dockerfile"), "w") as f:
    f.write(dockerfile)

# ─── .dockerignore ─────────────────────────────────────────────────────────────
dockerignore = """__pycache__/
*.pyc
.env
output/
.git/
"""

with open(os.path.join(base, ".dockerignore"), "w") as f:
    f.write(dockerignore)

print("submit_job.py, Dockerfile, .dockerignore written")
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp/")