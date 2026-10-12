"""Compare NLI model candidates on data/nli_pairs.jsonl (author-written pairs, 20 items).

    python scripts/compare_nli_models.py [model ...]   # default: all NLI candidates in the registry

Reports accuracy, per-class recall, latency and memory. The pairs are illustrative, not a
benchmark: they catch a broken model, they do not prove a good one.
"""
import gc
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import psutil  # noqa: E402

from speakwise.config import PipelineConfig  # noqa: E402
from speakwise.models import REGISTRY  # noqa: E402
from speakwise.onnx_models import OnnxNLI  # noqa: E402


def main(names):
    pairs = [json.loads(l) for l in (ROOT / "data" / "nli_pairs.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    proc = psutil.Process(os.getpid())
    results = {}
    for name in names:
        gc.collect()
        before = proc.memory_info().rss
        t0 = time.perf_counter()
        nli = OnnxNLI(PipelineConfig(nli_model=name))
        load = time.perf_counter() - t0
        t1 = time.perf_counter()
        preds = nli.predict([(p["premise"], p["hypothesis"]) for p in pairs])
        per = (time.perf_counter() - t1) / len(pairs) * 1000
        binary = "contradiction" not in nli.labels
        correct, recall = 0, Counter()
        for p, pr in zip(pairs, preds):
            top = max(pr, key=pr.get)
            gold = p["label"]
            if binary:  # entailment vs not_entailment
                gold = "entailment" if gold == "entailment" else "not_entailment"
            ok = top == gold
            correct += ok
            recall[(gold, ok)] += 1
        classes = sorted({g for g, _ in recall})
        results[name] = {
            "accuracy": round(correct / len(pairs), 3),
            "recall": {c: f"{recall[(c, True)]}/{recall[(c, True)] + recall[(c, False)]}" for c in classes},
            "binary_only": binary, "load_s": round(load, 2), "ms_per_pair": round(per, 1),
            "rss_increase_mb": round((proc.memory_info().rss - before) / 2**20),
            "size_mb": REGISTRY[name]["size_mb"], "license": REGISTRY[name]["license"]}
        print(name, json.dumps(results[name]), flush=True)
        del nli
    out = ROOT / "outputs" / "nli_model_comparison.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    default = [n for n, s in REGISTRY.items() if "NLI" in s["purpose"]]
    main(sys.argv[1:] or default)
