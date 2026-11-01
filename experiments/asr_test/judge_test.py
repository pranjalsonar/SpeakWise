"""Run the POC's LLM relevance judge against a hosted Groq model.

Usage:  python judge_test.py MATERIAL.txt TOPIC [WORDS_JSON] [MODEL]

WORDS_JSON defaults to out/groq_words.json (written by compare_asr.py).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

from compare_asr import OUT_DIR, load_env

DEFAULT_MODEL = "openai/gpt-oss-120b"


def judge_prompt(topic, material, transcript):
    # Same prompt as judge_relevance() in the POC's content.py.
    material_words = material.split()
    if len(material_words) > 3500:
        material = " ".join(material_words[:3500])
    return (
        f"TOPIC: {topic}\n\nREADING MATERIAL:\n{material}\n\n"
        f"SPEECH TRANSCRIPT:\n{transcript}\n\n"
        "The speaker read the material and then gave a short talk. Judge whether the "
        "talk is in context with the topic and the material. The talk does not need to "
        "repeat the material word for word; paraphrases, opinions and relevant examples "
        "count as on-topic. Ignore filler words and grammar.\n\n"
        "Reply with ONLY a JSON object with these keys:\n"
        '{"score": <integer 0-100, how relevant the talk is to the topic/material>, '
        '"covered_points": [<up to 5 short phrases: material ideas the speaker covered>], '
        '"missed_points": [<up to 3 short phrases: important ideas they could add>], '
        '"off_topic": [<up to 3 short phrases: parts of the talk unrelated to the topic>]}'
    )


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    material = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
    topic = sys.argv[2]
    words_json = Path(sys.argv[3]) if len(sys.argv) > 3 else OUT_DIR / "groq_words.json"
    model = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_MODEL
    transcript = json.loads(words_json.read_text(encoding="utf-8"))["transcript"]

    load_env()
    t0 = time.time()
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a strict but fair public-speaking coach."},
                {"role": "user", "content": judge_prompt(topic, material, transcript)},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if not resp.ok:
        raise SystemExit(f"{resp.status_code}: {resp.text[:500]}")
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    print(f"model: {model}   latency: {time.time() - t0:.1f}s   usage: {data.get('usage')}")
    print(json.dumps(json.loads(match.group(0)), indent=2) if match else text)


if __name__ == "__main__":
    main()
