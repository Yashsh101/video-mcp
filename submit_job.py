#!/usr/bin/env python3
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
    print(f"\n✅ Job submitted: {job['job_id']} | Video: {job['video_id']}")
    print(f"   {job['message']}\n")

    if stream:
        print("📡 Streaming pipeline progress via SSE...")
        with httpx.stream("GET", f"{API_BASE}/api/stream/{job['job_id']}") as r:
            for line in r.iter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if data.get("done"):
                        print(f"\n🏁 Pipeline {data['status'].upper()}")
                        break
                    print(f"   [{data.get('progress', 0):3d}%] {data.get('step', '')}")
    else:
        print("📊 Poll with:")
        print(f"   curl http://localhost:8000/api/status/{job['job_id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", help="Path to payload JSON file")
    parser.add_argument("--stream", action="store_true", help="Stream SSE progress")
    args = parser.parse_args()
    submit(args.payload, args.stream)
