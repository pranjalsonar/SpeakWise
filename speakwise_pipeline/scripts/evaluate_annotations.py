"""Score a pipeline report against a human annotation of the same recording.

    python scripts/evaluate_annotations.py outputs/report_<id>.json annotations/<id>.json [--tolerance 0.5]

Event matching: a detected event matches an annotated one if their intervals overlap, or
their centres are within the tolerance. Reports precision / recall / F1 per event type and
word error rate (WER) of the transcript. Results describe ONE recording; aggregate several
before drawing conclusions.
"""
import argparse
import json
import re
from pathlib import Path


def match(pred, gold, tol):
    used, tp = set(), 0
    for p in pred:
        for j, g in enumerate(gold):
            if j in used:
                continue
            overlap = p["start"] < g["end"] and p["end"] > g["start"]
            near = abs((p["start"] + p["end"]) / 2 - (g["start"] + g["end"]) / 2) <= tol
            if overlap or near:
                used.add(j)
                tp += 1
                break
    fp, fn = len(pred) - tp, len(gold) - tp
    prec = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1}


def wer(ref: str, hyp: str) -> float:
    norm = lambda s: re.findall(r"[a-z']+", s.lower())  # noqa: E731
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)] / max(len(r), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("annotation")
    ap.add_argument("--tolerance", type=float, default=0.5)
    a = ap.parse_args()
    rep = json.loads(Path(a.report).read_text(encoding="utf-8"))
    ann = json.loads(Path(a.annotation).read_text(encoding="utf-8"))
    aa = rep["audio_analysis"]
    ev = lambda xs: [{"start": x["start"], "end": x["end"]} for x in xs]  # noqa: E731
    gold_rep = [x for x in ann.get("repetitions", []) if x.get("type", "accidental") == "accidental"]
    pred_rep = [x for x in (aa.get("repetitions") or {}).get("events", []) if x["type"] in ("word_repetition", "phrase_repetition")]
    results = {
        "fillers": match(ev((aa.get("fillers") or {}).get("events", [])), ev(ann.get("fillers", [])), a.tolerance),
        "repetitions": match(ev(pred_rep), ev(gold_rep), a.tolerance),
        "pauses": match(ev((aa.get("pauses") or {}).get("events", [])), ev(ann.get("pauses", [])), a.tolerance),
    }
    if ann.get("reference_transcript"):
        results["word_error_rate"] = round(wer(ann["reference_transcript"], rep["transcription"]["text"]), 3)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
