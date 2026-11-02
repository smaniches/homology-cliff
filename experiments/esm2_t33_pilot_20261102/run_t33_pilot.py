#!/usr/bin/env python3
"""Actual-model ESM-2 t33 extraction pilot, not a benchmark score.

Inputs are frozen Homology Cliff sequences. Outputs are isolated, and no
dataset, preregistration, published result or model weights are modified.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys

import numpy as np
import torch

DATASET = Path("data/sequences/proteins_25k_sequences.json")
DATASET_SHA256 = "c99d8329c02b806b9d208465946c68826d17245cd9e012ca9a7b94faea0a60fc"
MODEL_ID = "facebook/esm2_t33_650M_UR50D"
MODEL_REVISION = "08e4846e537177426273712802403f7ba8261b6c"
SAMPLE_INDICES = (4670, 14847, 24533, 10775, 5190, 23445)
EXPECTED_LENGTHS = (5, 78, 184, 516, 703, 995)
OUTPUT_DIR = Path(os.environ.get("PILOT_OUTPUT_DIR", "pilot-out"))


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sequences(path: Path) -> list[str]:
    if digest_file(path) != DATASET_SHA256:
        raise RuntimeError("Frozen dataset SHA-256 mismatch. Refusing inference.")
    with path.open(encoding="utf-8") as f:
        obj = json.load(f)
    rows = obj["test_set"]
    if len(rows) != 24885:
        raise RuntimeError("Unexpected frozen dataset cardinality")
    seqs = [rows[i]["sequence"] for i in SAMPLE_INDICES]
    if any(not isinstance(seq, str) or len(seq) != length
           for seq, length in zip(seqs, EXPECTED_LENGTHS)):
        raise RuntimeError("Dataset row identities or selected lengths changed")
    if len(set(SAMPLE_INDICES)) != len(SAMPLE_INDICES):
        raise RuntimeError("Duplicate sample index")
    return seqs


def residue_mask(input_ids: torch.Tensor, attention_mask: torch.Tensor,
                 cls_id: int, eos_id: int, pad_id: int) -> torch.Tensor:
    if input_ids.shape != attention_mask.shape or input_ids.ndim != 1:
        raise ValueError("Expected matching one-dimensional token and attention arrays")
    return (attention_mask.bool() & (input_ids != cls_id) &
            (input_ids != eos_id) & (input_ids != pad_id))


def normalized_mean(hidden: torch.Tensor, mask: torch.Tensor) -> np.ndarray:
    if hidden.ndim != 2 or mask.ndim != 1 or hidden.shape[0] != mask.shape[0]:
        raise ValueError("Invalid hidden-state and pooling-mask shapes")
    if int(mask.sum().item()) < 1:
        raise ValueError("Cannot pool an empty residue set")
    vec = hidden[mask].to(dtype=torch.float32).mean(dim=0).cpu().numpy().astype(np.float64)
    norm = float(np.linalg.norm(vec))
    if not np.isfinite(norm) or norm <= 1e-12:
        raise ValueError("Invalid embedding norm")
    result = (vec / norm).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Non-finite normalized embedding")
    return result


def extract(encoded: dict, hidden: torch.Tensor, tokenizer, expected_length: int):
    ids = encoded["input_ids"][0]
    att = encoded["attention_mask"][0]
    mask = residue_mask(ids, att, tokenizer.cls_token_id,
                        tokenizer.eos_token_id, tokenizer.pad_token_id)
    if int(mask.sum()) != expected_length:
        raise RuntimeError(f"Unexpected residue count: {int(mask.sum())} != {expected_length}")
    residue = normalized_mean(hidden, mask)
    legacy = normalized_mean(hidden, att.bool())
    return residue, float(np.dot(residue.astype("float64"), legacy.astype("float64")))


def save_output(embedding: np.ndarray, manifest: dict, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if any((root / name).exists() for name in ("pilot_embedding.npy", "pilot_result.json")):
        raise FileExistsError("Refusing to overwrite existing pilot evidence")
    tmp = root / "pilot_embedding.npy.part"
    try:
        with tmp.open("wb") as f:
            np.save(f, embedding, allow_pickle=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, root / "pilot_embedding.npy")
        manifest["embedding_sha256"] = digest_file(root / "pilot_embedding.npy")
        text = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
        mtmp = root / "pilot_result.json.part"
        with mtmp.open("w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(mtmp, root / "pilot_result.json")
    finally:
        if tmp.exists():
            tmp.unlink()


def run() -> None:
    from transformers import EsmModel, EsmTokenizer

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    torch.set_num_threads(2)
    revision = MODEL_REVISION
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise RuntimeError("Could not freeze model revision")
    seqs = load_sequences(DATASET)
    tokenizer = EsmTokenizer.from_pretrained(MODEL_ID, revision=revision)
    model = EsmModel.from_pretrained(MODEL_ID, revision=revision, use_safetensors=True).eval()
    model = model.to("cpu")
    vectors, comparisons = [], []
    with torch.inference_mode():
        for number, (index, sequence) in enumerate(zip(SAMPLE_INDICES, seqs), start=1):
            encoded = tokenizer(sequence, return_tensors="pt", add_special_tokens=True,
                                truncation=False)
            hidden = model(**encoded).last_hidden_state[0]
            vector, legacy_cosine = extract(encoded, hidden, tokenizer, len(sequence))
            if vector.shape != (1280,) or not np.isfinite(vector).all():
                raise RuntimeError(f"Invalid embedding shape/data at row {index}")
            vectors.append(vector)
            comparisons.append(legacy_cosine)
            print(f"PILOT_PROGRESS {number}/{len(seqs)} row={index} residues={len(sequence)} "
                  f"cosine_legacy={legacy_cosine:.10f}", flush=True)

        encoded_batch = tokenizer(seqs[:2], return_tensors="pt", padding=True,
                                  truncation=False)
        batched_states = model(**encoded_batch).last_hidden_state
        deltas = []
        for j in range(2):
            encoded_row = {k: v[j:j+1] for k,v in encoded_batch.items()}
            vector, _ = extract(encoded_row, batched_states[j], tokenizer, len(seqs[j]))
            delta = float(np.linalg.norm(vector.astype(np.float64)
                                         - vectors[j].astype(np.float64)))
            deltas.append(delta)
        if max(deltas) > 1e-3:
            raise RuntimeError(f"Padding invariance failure (L2 deltas={deltas})")

    embedding = np.stack(vectors).astype(np.float32)
    norms = np.linalg.norm(embedding, axis=1)
    if embedding.shape != (6, 1280) or not np.all(np.abs(norms - 1.0) < 2e-6):
        raise RuntimeError("Output cardinality, dimensionality or normalization error")

    result = {
        "status": "T33_FROZEN_EMBEDDING_PILOT_ONLY",
        "source_hash": DATASET_SHA256,
        "model_id": MODEL_ID, "model_revision": revision,
        "source_revision": os.environ.get("GITHUB_SHA"),
        "selected_indices": list(SAMPLE_INDICES),
        "selected_lengths": list(EXPECTED_LENGTHS),
        "actual_output_shape": list(embedding.shape),
        "pooling": "residue-only mean excluding CLS/EOS/PAD, then L2 normalize",
        "float_precision": "fp32, CPU",
        "unit_norms": [float(v) for v in norms],
        "cosine_vs_special_token_pooling": comparisons,
        "batch_invariance_l2": deltas,
        "environment": {
            "python": sys.version.split()[0], "torch": torch.__version__,
            "numpy": np.__version__, "transformers": importlib.metadata.version("transformers"),
            "huggingface_hub": importlib.metadata.version("huggingface-hub"),
        },
        "limitations": [
            "Only six prespecified proteins, not the 24,885-protein benchmark.",
            "No biological scores, no training, and no superiority claim.",
            "Model revision is frozen at run start and recorded in this manifest.",
            "Precision and batch invariance apply only to this CPU reference execution.",
        ]
    }
    save_output(embedding, result, OUTPUT_DIR)
    print("PILOT_DONE=" + json.dumps({"shape": result["actual_output_shape"],
                                    "model_revision": revision,
                                    "max_batch_delta": max(deltas),
                                    "output_dir": str(OUTPUT_DIR)}), flush=True)


if __name__ == "__main__":
    run()
