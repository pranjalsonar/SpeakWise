"""Lightweight ONNX wrappers (onnxruntime + tokenizers, no PyTorch) for the context models.

* Embedder: all-MiniLM-L6-v2, mean pooling, L2-normalised (cosine = dot product).
  Adapted from backend/app/analysis/context/embedder.py.
* NLI: cross-encoder/nli-deberta-v3-xsmall. Returns probabilities for
  contradiction / entailment / neutral (label order read from the model's config.json).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from speakwise import models
from speakwise.config import PipelineConfig


def _session(path: Path, threads: int = 1):
    import onnxruntime as ort

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = threads
    opts.inter_op_num_threads = 1
    opts.enable_cpu_mem_arena = False  # lower peak memory on small machines
    return ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])


class OnnxEmbedder:
    def __init__(self, cfg: Optional[PipelineConfig] = None, max_tokens: int = 128):
        from tokenizers import Tokenizer

        cfg = cfg or PipelineConfig()
        self.name = cfg.embed_model
        main = models.ensure(cfg.embed_model, cfg)
        root = models.model_dir(cfg.embed_model, cfg)
        self._sess = _session(main)
        self._inputs = {i.name for i in self._sess.get_inputs()}
        self._tok = Tokenizer.from_file(str(root / "tokenizer.json"))
        self._tok.enable_truncation(max_length=max_tokens)
        self._tok.enable_padding(pad_id=0, pad_token="[PAD]")

    def encode(self, texts: list[str], batch: int = 16) -> np.ndarray:
        out = []
        for i in range(0, len(texts), batch):
            enc = self._tok.encode_batch(texts[i:i + batch])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self._inputs:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self._sess.run(None, feeds)[0]
            m = mask[..., None].astype(np.float32)
            pooled = (hidden * m).sum(1) / np.maximum(m.sum(1), 1e-9)
            out.append(pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9))
        return np.vstack(out).astype(np.float32) if out else np.zeros((0, 384), np.float32)


class OnnxNLI:
    def __init__(self, cfg: Optional[PipelineConfig] = None, max_tokens: int = 256):
        from tokenizers import Tokenizer

        cfg = cfg or PipelineConfig()
        self.name = cfg.nli_model
        main = models.ensure(cfg.nli_model, cfg)
        root = models.model_dir(cfg.nli_model, cfg)
        self._sess = _session(main)
        self._inputs = {i.name for i in self._sess.get_inputs()}
        tok = Tokenizer.from_file(str(root / "tokenizer.json"))
        tok.enable_truncation(max_length=max_tokens)
        tok.enable_padding(pad_id=tok.token_to_id("[PAD]") or 0, pad_token="[PAD]")
        self._tok = tok
        id2label = json.loads((root / "config.json").read_text(encoding="utf-8"))["id2label"]
        self.labels = [id2label[str(i)].lower() for i in range(len(id2label))]

    def predict(self, pairs: list[tuple[str, str]], batch: int = 8) -> list[dict[str, float]]:
        """pairs: (premise, hypothesis). Returns one {label: probability} per pair."""
        out: list[dict[str, float]] = []
        for i in range(0, len(pairs), batch):
            enc = self._tok.encode_batch(pairs[i:i + batch])
            feeds = {"input_ids": np.array([e.ids for e in enc], dtype=np.int64),
                     "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64)}
            if "token_type_ids" in self._inputs:
                feeds["token_type_ids"] = np.array([e.type_ids for e in enc], dtype=np.int64)
            logits = self._sess.run(None, feeds)[0]
            p = np.exp(logits - logits.max(axis=1, keepdims=True))
            p /= p.sum(axis=1, keepdims=True)
            out += [{lab: float(row[j]) for j, lab in enumerate(self.labels)} for row in p]
        return out
