"""Video analysis pipeline (POC).

Self-contained: nothing in this package imports FastAPI, the database or
app.core.config, so it runs standalone (CLI) and can be wired into a route
and service later.

Phases:
    1. preprocess  - video -> 16 kHz mono WAV + frames @ 10 fps + metadata
    2. audio       - VAD, ASR, fillers, pauses, prosody -> audio_analysis.json
    3. vision      - eye contact, posture, hands -> vision_analysis.json
    4. fusion      - unified timeline, metrics, scores -> session_report.json
    5. feedback    - issues + tips retrieval + vocabulary + optional LLM -> final_report.json

Shared clock: every timestamp is in seconds from the start of the video.
Frame i is at i / frame_fps seconds; audio sample n is at n / sample_rate.
"""
