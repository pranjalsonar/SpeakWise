"""Run the context evaluator over data/context_eval/seed.jsonl and compare with the expectations.

    python scripts/evaluate_context.py [--nli MODEL] [--no-nli]

IMPORTANT: the seed examples and their expectations were written by the pipeline author
("illustrative_author_written"). Agreement with them shows the rubric behaves as designed;
it is NOT a measured accuracy. Real evaluation needs human-rated examples (annotations/).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from speakwise.config import PipelineConfig  # noqa: E402
from speakwise.context_matching import evaluate_context  # noqa: E402
from speakwise.onnx_models import OnnxEmbedder, OnnxNLI  # noqa: E402

RELEVANCE_ORDER = {"low": 0, "partial": 1, "high": 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nli", default=None)
    ap.add_argument("--no-nli", action="store_true")
    args = ap.parse_args()
    cfg = PipelineConfig(**({"nli_model": args.nli} if args.nli else {}))
    base = ROOT / "data" / "context_eval"
    materials = json.loads((base / "materials.json").read_text(encoding="utf-8"))
    examples = [json.loads(l) for l in (base / "seed.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    emb = OnnxEmbedder(cfg)
    nli = None if args.no_nli else OnnxNLI(cfg)

    rows, kp_tp, kp_fp, kp_fn = [], 0, 0, 0
    inc_hit = inc_total = inc_false = 0
    for ex in examples:
        m = materials[ex["material"]]
        text = (base / m["file"]).read_text(encoding="utf-8")
        ce = evaluate_context(m["topic"], text, ex["transcript"], cfg, speaking_duration_s=ex.get("duration_s"),
                              key_points=m["key_points"], embedder=emb, nli=nli)
        exp = ex["expected"]
        covered = {k.id for k in ce.key_points if k.covered}
        want = set(exp.get("covered_key_points", []))
        if exp["relevance"] != "unreliable":
            kp_tp += len(covered & want)
            kp_fp += len(covered - want)
            kp_fn += len(want - covered)
        flagged = [c.text for c in ce.claims if c.label == "potentially_inconsistent"]
        for needle in exp.get("inconsistent_claims", []):
            inc_total += 1
            inc_hit += any(needle.lower() in f.lower() for f in flagged)
        inc_false += sum(1 for f in flagged if not any(n.lower() in f.lower() for n in exp.get("inconsistent_claims", [])))
        rows.append({
            "id": ex["id"], "expected_relevance": exp["relevance"], "status": ce.status.value,
            "relevance": ce.topic_relevance.value, "coverage_adj": ce.key_point_coverage_adjusted.value,
            "alignment": ce.context_alignment.value, "verdict": ce.verdict,
            "off_topic_units": len(ce.off_topic_segments), "claims": ce.consistency_counts,
            "key_points_covered": sorted(covered), "key_points_expected": sorted(want)})

    print(f"{'example':34s} {'expect':10s} {'status':11s} {'relev':>6s} {'cov':>6s} {'align':>6s}  claims")
    for r in rows:
        f = lambda v: f"{v:6.1f}" if v is not None else "     -"  # noqa: E731
        print(f"{r['id']:34s} {r['expected_relevance']:10s} {r['status']:11s} {f(r['relevance'])} {f(r['coverage_adj'])} "
              f"{f(r['alignment'])}  {r['claims']}")

    rated = [r for r in rows if r["expected_relevance"] in RELEVANCE_ORDER and r["relevance"] is not None]
    pairs = ok = 0
    for a in rated:
        for b in rated:
            if RELEVANCE_ORDER[a["expected_relevance"]] > RELEVANCE_ORDER[b["expected_relevance"]]:
                pairs += 1
                ok += a["relevance"] > b["relevance"]
    prec = kp_tp / (kp_tp + kp_fp) if kp_tp + kp_fp else None
    rec = kp_tp / (kp_tp + kp_fn) if kp_tp + kp_fn else None
    summary = {
        "label": "PRELIMINARY - agreement with author-written expectations, not human-rated accuracy",
        "examples": len(rows),
        "relevance_ordering_agreement": f"{ok}/{pairs}",
        "unreliable_examples_flagged": [r["id"] for r in rows if r["expected_relevance"] == "unreliable" and r["status"] == "unavailable"],
        "key_point_precision": round(prec, 3) if prec is not None else None,
        "key_point_recall": round(rec, 3) if rec is not None else None,
        "inconsistency_found": f"{inc_hit}/{inc_total}", "inconsistency_false_flags": inc_false,
        "nli_model": None if nli is None else cfg.nli_model}
    print(json.dumps(summary, indent=2))
    out = ROOT / "outputs" / "context_eval_results.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
