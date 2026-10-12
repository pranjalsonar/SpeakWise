# Integrating the SpeakWise pipeline into the desktop app

For the desktop-app developer. The pipeline is a normal Python package (`speakwise`). The app
installs it, calls **one function**, and gets back a validated report object (or JSON). No server,
database or Colab is involved; everything runs on the user's computer.

---

## 1. Install

Requirements on the user's machine:

| Need | Notes |
|---|---|
| Python 3.10+ | Tested on 3.10 (Windows) and 3.13 (Linux/Colab). |
| **FFmpeg + ffprobe on PATH** | Not a pip package. Bundle it with the installer or ask users to install it. Without it every analysis fails at the input stage. |
| RAM | About 3 GB free for the default settings; see section 6 for low-memory machines. |
| Disk | About 300 MB of models plus the Whisper model (75-480 MB), downloaded on first use. |

```bash
pip install "git+https://github.com/pranjalsonar/SpeakWise.git@<commit-or-tag>#subdirectory=speakwise_pipeline"
```

Always pin a commit hash or tag (ask Pranjal for the current one) so pipeline changes never
break the app unexpectedly.

---

## 2. The one call

```python
from pathlib import Path
from speakwise.config import PipelineConfig
from speakwise.pipeline import process_session

cfg = PipelineConfig(
    models_dir=APP_DATA / "speakwise_models",    # set these two explicitly (see section 7)
    output_dir=APP_DATA / "speakwise_reports",
)
report = process_session(
    "recording.mp4",              # one MP4 with audio + video
    topic="Climate change: causes, effects and what we can do",
    reading_material=material_text,  # the EXACT text shown to the user before speaking
    speaking_duration=180,        # seconds the user chose (60/180/300), or None
    config=cfg,
    save=True,                    # also writes report_<session_id>.json to output_dir
)

report.model_dump()   # plain dict for the UI
report.to_json()      # JSON string
```

`process_session` **does not raise** for bad recordings or model failures. It always returns a
report; problems are listed in `report.errors` / `report.warnings`, and the affected sections get a
status. It only raises `ValueError` for invalid arguments (and `KeyboardInterrupt` if interrupted).

---

## 3. Run it off the UI thread (required)

Analysis takes seconds on a GPU and roughly 1-3 minutes on a laptop CPU, and the speech model
needs a lot of memory. Run it in a **separate process** so the window never freezes and an
out-of-memory crash cannot take the app down:

```python
import multiprocessing as mp

def _analyse(queue, mp4, topic, material, duration, cfg_dict):
    from speakwise.config import PipelineConfig
    from speakwise.pipeline import process_session
    try:
        rep = process_session(mp4, topic, material, duration, PipelineConfig.from_dict(cfg_dict))
        queue.put(("result", rep.to_json()))
    except Exception as exc:
        queue.put(("error", f"{type(exc).__name__}: {exc}"))

def start_analysis(mp4, topic, material, duration, cfg_dict):
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    proc = ctx.Process(target=_analyse, args=(queue, mp4, topic, material, duration, cfg_dict), daemon=True)
    proc.start()
    return proc, queue   # poll queue.get_nowait() from a QTimer / Tk after(); proc.terminate() to cancel
```

* On Windows the app's entry script needs `if __name__ == "__main__":`, and frozen apps
  (PyInstaller) need `multiprocessing.freeze_support()`.
* If the child process dies without sending a message (`proc.exitcode != 0`), treat it as
  "the computer ran out of memory" and suggest the low-memory settings in section 6.
* Rebuild the report in the UI process with
  `SessionReport.model_validate_json(json_text)` (from `speakwise.schemas`).

Coming in the next update (not yet pushed): a `progress(stage, fraction)` callback on
`process_session` and a ready-made worker class, so you won't need the code above.

---

## 4. Reading the report

Top-level sections (full schema: `configs/report.schema.json`, version in
`report.session_metadata.schema_version`):

| Section | What to show |
|---|---|
| `input_validation` | Whether the file was usable; `checks` lists each test. |
| `transcription` | `text`, `words` (each with start/end time and probability). |
| `audio_analysis` | `fillers`, `repetitions`, `pauses`, `clarity`, `audio_quality`, `words_per_minute`. |
| `video_analysis` | `face_visible_pct`, `camera_directed_gaze_pct`, `head_orientation`, `posture`. |
| `context_evaluation` | `topic_relevance`, `key_point_coverage_adjusted`, `key_points`, `claims`, `off_topic_segments`, `context_alignment`, `verdict`. |
| `improvement_suggestions` | Ready-to-display tips, each with `evidence` and `moments` (timestamps). |
| `warnings`, `errors` | Show these; they explain missing results. |

**Every number is a `Metric`:**

```json
{"value": 6.2, "unit": "per_minute", "status": "ok", "denominator": "speech span 29.2s", "note": null}
```

| `status` | Meaning | UI should show |
|---|---|---|
| `ok` | Measured | the value |
| `warning` | Measured with a caveat (read `note`) | the value + a small "estimate" marker |
| `unavailable` | Not enough evidence (no face, no speech...) | "Not measured" + `note`, **never 0** |
| `failed` | Processing error | "Could not measure" |
| `skipped` | Disabled in config | hide |

A value of `0` with status `ok` is a real zero (e.g. no fillers). A missing measurement always
has `value: null`.

**Timestamps** (event `start`/`end`, word times, suggestion `moments`) are seconds from the start of
the MP4, so they can be used directly to seek a video player.

**Things the UI must not over-claim:**

* Camera gaze is an *estimate*; "not visible" is not "bad eye contact".
* `context_alignment` / `verdict` use a **provisional** 70/100 target that has not been validated.
* A claim labelled `not_addressed` is *not* wrong; only `potentially_inconsistent` claims are worth
  flagging, and as "check against the reading", not "false".
* There is no overall "confidence" score on purpose.

---

## 5. Inputs the app must provide

* **One MP4** containing both audio and video (the app records it). Other containers work with a
  warning. Supported length: 3 s to 15 min.
* **The exact reading material** shown to the user. Do not summarise or regenerate it; the
  context score compares against this text. The report stores only its SHA-256 hash.
* Optional `key_points=[...]` if the app has curated main points; otherwise they are extracted.
* Ask users to look at the camera with head and shoulders in frame; posture is only measured
  when both shoulders are visible.

---

## 6. Low-memory computers

Many student laptops have less than 2 GB of free RAM. Use the provided low-memory profile:

```python
cfg = PipelineConfig.from_json("<path>/configs/low_memory_cpu.json")
# or: PipelineConfig(asr_model="tiny", asr_cpu_threads=2, video_sample_fps=3, pose_enabled=False)
```

If transcription still fails, the report has `transcription.status == "failed"` and an entry in
`errors`; pauses and recording quality are still measured.

---

## 7. Known issues for app integration

* **Set `models_dir` and `output_dir` explicitly.** Their defaults point inside the source folder,
  which is wrong for a pip-installed package. Use the app's data folder (e.g. `%APPDATA%\SpeakWise`).
* Models download on first analysis (needs internet once). To avoid a slow first run, call
  `from speakwise import models; [models.ensure(n, cfg) for n in models.defaults(cfg)]` during app
  setup. Set `allow_downloads=False` afterwards to fail clearly instead of downloading.
* Temporary audio is deleted after each run. If you kill the child process, delete its
  `work_dir` yourself (set `work_dir` per job to make this easy).
* Accuracy has not yet been measured on real recordings; treat all results as preliminary.

---

## 8. Quick check that everything works

```bash
python -c "from speakwise.environment import inspect_environment; import json; print(json.dumps(inspect_environment(), indent=1))"
python scripts/generate_test_fixture.py --out test_fixture   # from a clone of the repo; needs espeak-ng or Windows speech
```

Then run `process_session("test_fixture/fixture.mp4", ...)`; you should see 3 fillers and 4 pauses.

Questions about the pipeline: Pranjal. Source and full documentation: `speakwise_pipeline/README.md`.
