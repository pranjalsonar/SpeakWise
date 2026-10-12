"""Generate notebooks/speakwise_pipeline_colab.ipynb (keeps the notebook reviewable as code).

    python scripts/build_notebook.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cells = []


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)})


def code(text):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": text.strip("\n").splitlines(keepends=True)})


md("""
# SpeakWise pipeline: Colab development notebook

Runs the `speakwise` package from the GitHub repository in a **fresh** runtime. Nothing here relies on
files surviving a reset: every session re-clones the code and re-downloads models.

**Privacy:** uploaded recordings and reports stay in this runtime (or your own Google Drive if you choose
to export). Nothing is sent to external APIs; all models run inside the runtime.

Run the cells in order. Sections 7-9 are optional experiments.
""")
md("## 1. Inspect the runtime (before installing anything)")
code("""
!python --version
!nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || echo "No GPU attached"
!free -h | head -2
!df -h /content | tail -1
!ffmpeg -version | head -1
!nproc
""")
md("## 2. Get the code (public repository, no credentials needed)")
code("""
REPO = "https://github.com/pranjalsonar/SpeakWise.git"
BRANCH = "poc_model"
%cd /content
# leave the folder before deleting it, so re-running this cell in the same runtime works
!rm -rf /content/SpeakWise
!git clone --quiet --depth 1 --branch {BRANCH} {REPO} /content/SpeakWise
%cd /content/SpeakWise/speakwise_pipeline
!git log --oneline -1
""")
md("## 3. Install dependencies")
code("""
!apt-get -qq update > /dev/null && apt-get -qq install -y espeak-ng > /dev/null && espeak-ng --version
!pip install -q -r requirements.txt
# faster-whisper's CTranslate2 needs CUDA 12 cuBLAS + cuDNN 9; Colab may ship a newer CUDA.
# The pipeline preloads these automatically (speakwise.environment.preload_cuda12_libs).
!nvidia-smi -L > /dev/null 2>&1 && pip install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" || echo "No GPU: CPU mode"
!pip install -q -e . --no-deps
# An editable install is only visible to NEW processes (scripts, pytest); make it importable in
# this already-running kernel too, without a runtime restart:
import sys
sys.path.insert(0, "/content/SpeakWise/speakwise_pipeline/src")
from speakwise.environment import inspect_environment, choose_asr
env = inspect_environment("/content")
import json; print(json.dumps({k: v for k, v in env.items() if k != "libraries"}, indent=1)); print(env["libraries"])
print("ASR choice:", choose_asr("auto", "auto", "auto", env))
""")
md("## 4. Download the default models (MiniLM 23 MB, NLI 253 MB, MediaPipe 10 MB; Whisper downloads on first use)")
code("""
!python -m speakwise.models download
""")
md("## 5. Run the automated tests (fast suite)")
code("""
!python -m pytest tests -q -p no:cacheprovider -m "not slow" 2>&1 | tail -15
""")
md("## 6. Synthetic fixture + full pipeline with the real speech recogniser")
code("""
import json, time
from pathlib import Path
from speakwise.fixtures import build_fixture
from speakwise.pipeline import process_session
from speakwise.config import PipelineConfig
from speakwise.summary import summarize

truth = build_fixture("outputs/fixture")
print("fixture:", truth["duration_s"], "s | pauses:", [p["duration_s"] for p in truth["pauses"]])
print("reference:", truth["reference_transcript"])
material = Path("data/context_eval/materials/climate_change.txt").read_text()
topic = truth["expected"]["topic"]
cfg = PipelineConfig(output_dir=Path("outputs/reports"))
t = time.time()
report = process_session("outputs/fixture/fixture.mp4", topic, material, speaking_duration=30, config=cfg)
print(f"done in {time.time() - t:.1f}s\\n")
print(summarize(report))
""")
code("""
from IPython.display import Audio, Video
Video("outputs/fixture/fixture.mp4", embed=True, width=320)
""")
md("""
## 7. Experiment: NLI model choice (consistency check)
Compares the NLI candidates on `data/nli_pairs.jsonl` (20 author-written pairs: catches a broken model,
does not prove a good one). The base model was chosen from this comparison plus the seed-set results.
""")
code("""
!python -m speakwise.models download all   # adds the other NLI candidates (~900 MB)
!python scripts/compare_nli_models.py
""")
md("## 8. Experiment: context evaluation on the seed set (PRELIMINARY: author-written expectations)")
code("""
!python scripts/evaluate_context.py
""")
md("""
## 9. Experiment: speech-recognition model trade-off
Word error rate against the fixture's reference script, time and memory per model. TTS speech is not
natural speech; repeat on real annotated recordings before choosing a model for production.
""")
code("""
import gc, json, psutil, time, numpy as np
from speakwise.config import PipelineConfig
from speakwise.audio_transcription import transcribe, release_models
from speakwise.media_preprocessing import preprocess_mp4
from speakwise.environment import inspect_environment
import importlib.util, sys
spec = importlib.util.spec_from_file_location("ev", "scripts/evaluate_annotations.py"); ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)

truth = json.load(open("outputs/fixture/ground_truth.json"))  # from section 6
prep = preprocess_mp4("outputs/fixture/fixture.mp4", PipelineConfig(keep_artifacts=False))
audio, rate = prep.load_audio(); prep.workspace.cleanup()
env = inspect_environment()
rows = []
for name in ["base", "small", "large-v3-turbo"]:
    release_models(); gc.collect()
    t = time.time()
    try:
        tr = transcribe(audio, rate, PipelineConfig(asr_model=name), env)
        rows.append({"model": name, "device": tr.model["device"], "load_s": tr.model["load_time_s"],
                     "decode_s": tr.model["decode_time_s"], "wer": round(ev.wer(truth["reference_transcript"], tr.text), 3),
                     "fillers_kept": sum(w.text.lower().strip(",.") in ("um", "uh") for w in tr.words),
                     "rss_gb": round(psutil.Process().memory_info().rss / 2**30, 2)})
    except Exception as e:
        rows.append({"model": name, "error": str(e)[:120]})
    print(rows[-1])
release_models()
""")
md("""
## 10. Analyse your own recording
Upload one MP4 (audio + video) **or** set `MP4_PATH` to a file in your Google Drive. Paste the exact
topic and reading material the speaker was given.
""")
code("""
MP4_PATH = ""            # e.g. "/content/drive/MyDrive/speakwise/talk.mp4"; leave empty to upload
TOPIC = "Climate change: causes, effects and what we can do"
READING_MATERIAL_PATH = "data/context_eval/materials/climate_change.txt"   # or paste text into READING_MATERIAL
READING_MATERIAL = ""
SPEAKING_DURATION_S = 60

if not MP4_PATH:
    from google.colab import files
    up = files.upload()
    MP4_PATH = next(iter(up))
material = READING_MATERIAL or Path(READING_MATERIAL_PATH).read_text()
real = process_session(MP4_PATH, TOPIC, material, speaking_duration=SPEAKING_DURATION_S,
                       config=PipelineConfig(output_dir=Path("outputs/reports")))
print(summarize(real))
""")
md("## 11. Inspect intermediate results")
code("""
r = real if "real" in globals() else report
print("Pauses:"); [print(" ", e.type, e.start, e.end, e.details) for e in r.audio_analysis.pauses.events]
print("Fillers:"); [print(" ", e.start, e.text, e.details) for e in r.audio_analysis.fillers.events]
print("Key points:"); [print(" ", k.covered, round(k.similarity, 2), k.text[:80]) for k in r.context_evaluation.key_points]
print("Claims:"); [print(" ", c.label, "|", c.text[:80]) for c in r.context_evaluation.claims]
print("Warnings:"); [print(" ", w.module, w.message) for w in r.warnings]
""")
md("## 12. Export (optional): copy reports to your Google Drive")
code("""
from google.colab import drive
drive.mount("/content/drive")
!mkdir -p /content/drive/MyDrive/speakwise_outputs && cp -r outputs/reports outputs/*.json /content/drive/MyDrive/speakwise_outputs/ 2>/dev/null; ls /content/drive/MyDrive/speakwise_outputs
""")

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "name": "python3"},
                                   "language_info": {"name": "python"}, "colab": {"provenance": []},
                                   "accelerator": "GPU"},
      "nbformat": 4, "nbformat_minor": 0}
out = ROOT / "notebooks" / "speakwise_pipeline_colab.ipynb"
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out, len(cells), "cells")
