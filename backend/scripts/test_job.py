"""Upload a video to a running backend and print the report.

Usage:  .venv\\Scripts\\python.exe scripts\\test_job.py VIDEO [TOPIC_ID] [FIRST_NAME] [BASE_URL]
Example: .venv\\Scripts\\python.exe scripts\\test_job.py "..\\demo videos\\test_demo_video_unicorn.mp4" unicorns Raj
"""
import json
import sys
import time
from pathlib import Path

import requests

video = Path(sys.argv[1])
topic = sys.argv[2] if len(sys.argv) > 2 else "unicorns"
name = sys.argv[3] if len(sys.argv) > 3 else "Raj"
base = sys.argv[4] if len(sys.argv) > 4 else "http://127.0.0.1:8000"

t0 = time.time()
with video.open("rb") as f:
    r = requests.post(f"{base}/jobs", files={"video": (video.name, f, "video/mp4")},
                      data={"topic_id": topic, "first_name": name}, timeout=300)
print("POST /jobs", r.status_code, f"{time.time() - t0:.1f}s")
r.raise_for_status()
job = r.json()

last = None
while job["status"] in ("queued", "running"):
    time.sleep(2)
    job = requests.get(f"{base}/jobs/{job['id']}", timeout=30).json()
    if job["step"] != last:
        print(f"  {time.time() - t0:6.1f}s  {job['step']:<18} {job['progress']:.0%}")
        last = job["step"]

print("status:", job["status"], f"total {time.time() - t0:.1f}s")
if job["status"] != "done":
    print("error:", job["error"])
    sys.exit(1)

rep = job["result"]
out = Path(__file__).resolve().parents[1] / "data" / "last_report.json"
out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
print("\nSUMMARY:", rep["summary"])
print("\nSCORES:", json.dumps(rep["scores"], indent=1))
print("\nCOACH:", json.dumps(rep["coach"], indent=1))
print("\nCONTEXT:", {k: rep["context"][k] for k in ("score", "embedding_score", "llm_score", "verdict")})
print("PROVIDERS:", rep["providers"], "WARNINGS:", rep["warnings"])
s, v = rep["speech"], rep["video"]
print("SPEECH:", {k: s[k] for k in ("word_count", "wpm", "filler_count", "filler_breakdown", "short_pause_count",
                                    "long_pause_count", "stutter_count", "mumbled_count", "clarity_pct",
                                    "pitch_variation_semitones", "loudness_dbfs")})
print("VIDEO:", {k: v[k] for k in ("frames_analyzed", "rotation_applied", "face_visible_pct", "eye_contact_pct",
                                   "looking_down_pct", "slouch_pct", "gesture_pct", "blinks_per_min")})
print("\nFull report:", out)
