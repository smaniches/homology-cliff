#!/usr/bin/env python3
"""Frozen ESM-2 t33 embedding extraction with checked, restartable shards.

Standalone research execution; never edits the original dataset or releases.
The extracted vectors use exactly the residue-only method of the verified t33 pilot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np

MODEL_ID = "facebook/esm2_t33_650M_UR50D"
MODEL_SHA = "08e4846e537177426273712802403f7ba8261b6c"
DATA_SHA = "c99d8329c02b806b9d208465946c68826d17245cd9e012ca9a7b94faea0a60fc"
N = 24885
D = 1280
ANCHOR_HASHES = {
    4670: "73a18796d0e2801574b8a69b24d3c2f7575673f6b63cfe8fff8cf259726d28fa",
    14847: "850b0f67fa38f1d4f1979893233b3769cd9f404ab76cf6b7bedf6506de999d71",
    24533: "88662387af9002ce469958899ff097c7ff7cf397a0c15c2e87ca95b4c4699346",
    10775: "9cfec3f413fe8e0aac6a5db440894b907d1fd330fddd0638b747cb35d9d7f722",
    5190: "ac99397652a73d11ccae6c1f39b7d509c87fc1ab9832353cd447ca2721ab2664",
    23445: "21e6ae6453430631efa33eba2fa1dc4c70e105e05f167611a36ea84b4fbf8278",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def shard_interval(rank, n_shards, total=N):
    if not isinstance(rank, int) or not isinstance(n_shards, int) or n_shards < 1 or not 0 <= rank < n_shards:
        raise ValueError("Invalid shard rank/count")
    if n_shards > total:
        raise ValueError("Empty shards disallowed")
    return total * rank // n_shards, total * (rank + 1) // n_shards


def read_dataset(path, expected_sha=DATA_SHA, expected_n=N):
    if sha256(path) != expected_sha:
        raise ValueError("FROZEN DATASET SHA256 MISMATCH")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)["test_set"]
    if len(data) != expected_n:
        raise ValueError("Dataset row count mismatch")
    return data


def norm_check(x):
    if x.ndim != 2 or x.shape[1] != D or x.dtype != np.float32 or not np.isfinite(x).all():
        raise ValueError("Invalid embedding shape/dtype/finiteness")
    if not np.all(np.abs(np.linalg.norm(x.astype(np.float64), axis=1) - 1) < 2e-6):
        raise ValueError("Invalid L2 normalization")


def save_atomic(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Refusing to replace evidence: {path}")
    temp = path.with_suffix(path.suffix + ".part")
    if temp.exists():
        raise FileExistsError(f"Unresolved interrupted write: {temp}")
    try:
        with temp.open("xb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def save_block(outdir, start, end, vectors, device):
    from io import BytesIO
    norm_check(vectors)
    if vectors.shape != (end - start, D):
        raise ValueError("Block cardinality mismatch")
    outdir = Path(outdir)
    npy = outdir / f"part_{start:05d}_{end:05d}.npy"
    manifest = outdir / f"part_{start:05d}_{end:05d}.json"
    if manifest.exists() or npy.exists():
        raise FileExistsError(f"Existing block, requires resume verification: {npy}")
    f = BytesIO()
    np.save(f, vectors, allow_pickle=False)
    save_atomic(npy, f.getvalue())
    info = {"schema": "homology-cliff/t33-shard/v1", "model": MODEL_ID,
            "model_revision": MODEL_SHA, "data_sha256": DATA_SHA,
            "start": start, "end": end, "n": end-start, "dim": D,
            "dtype": "float32", "device": device, "file": npy.name,
            "npy_sha256": sha256(npy)}
    save_atomic(manifest, (json.dumps(info, indent=2, sort_keys=True) + "\n").encode())
    return info


def verify_block(manifest_path, expected_device=None):
    manifest_path = Path(manifest_path)
    info = json.loads(manifest_path.read_text())
    if (info.get("schema") != "homology-cliff/t33-shard/v1" or
        info.get("model_revision") != MODEL_SHA or info.get("model") != MODEL_ID or
        info.get("data_sha256") != DATA_SHA or info.get("dim") != D or
        info.get("dtype") != "float32" or info.get("n") != info.get("end")-info.get("start") or
        not 0 <= info.get("start", -1) < info.get("end", -1) <= N):
        raise ValueError("Invalid or incompatible block manifest")
    if expected_device is not None and info.get("device") != expected_device:
        raise ValueError("Mixed extraction devices disallowed")
    if Path(info["file"]).name != info["file"]:
        raise ValueError("Unsafe relative path")
    p = manifest_path.parent / info["file"]
    if sha256(p) != info["npy_sha256"]:
        raise ValueError("Corrupted block hash")
    x = np.load(p, mmap_mode="r", allow_pickle=False)
    if x.shape != (info["n"], D):
        raise ValueError("Block shape mismatch")
    norm_check(x)
    return info, x


def assemble(directory, output):
    """Refuse gaps, duplicate indices, mixed parameters, corrupt or extra blocks."""
    directory, output = Path(directory), Path(output)
    manifests = sorted(directory.rglob("part_*.json"))
    if not manifests:
        raise ValueError("No input blocks")
    pieces = []
    for path in manifests:
        info, x = verify_block(path, expected_device="cpu")
        pieces.append((info["start"], info["end"], path, x))
    pieces.sort(key=lambda p: p[0])
    offset = 0
    for start, end, _, _ in pieces:
        if start != offset:
            raise ValueError(f"Missing/overlapping rows: expected {offset}, got {start}")
        offset = end
    if offset != N:
        raise ValueError(f"Incomplete output, last row {offset} != {N}")
    output.mkdir(parents=True, exist_ok=True)
    dest = output / "embeddings_t33.npy"
    result = output / "MANIFEST.json"
    if dest.exists() or result.exists():
        raise FileExistsError("Will not overwrite existing final evidence")
    stage = output / "embeddings_t33.npy.part"
    if stage.exists():
        raise FileExistsError("Unresolved staged final output")
    try:
        with stage.open("xb") as fp:
            np.lib.format.write_array_header_2_0(fp, {"descr": np.lib.format.dtype_to_descr(np.dtype("<f4")),
                                                    "fortran_order": False, "shape": (N, D)})
            for start, end, path, x in pieces:
                fp.write(np.asarray(x, dtype="<f4").tobytes(order="C"))
            fp.flush()
            os.fsync(fp.fileno())
        # Independently reopen assembled .npy and verify all rows.
        whole = np.load(stage, mmap_mode="r", allow_pickle=False)
        if whole.shape != (N, D):
            raise ValueError("Final array invalid")
        norm_check(whole)
        for start, end, _, x in pieces:
            if not np.array_equal(whole[start:end], np.asarray(x)):
                raise ValueError("Assembly changed array bytes")
        os.replace(stage, dest)
        doc = {"schema": "homology-cliff/t33-combined/v1", "rows": N, "dim": D,
               "model": MODEL_ID, "model_revision": MODEL_SHA,
               "data_sha256": DATA_SHA, "output_sha256": sha256(dest),
               "algorithm": "single-sequence FP32 CPU, residue mean excluding CLS/EOS/PAD, L2-normalize",
               "parts": [{"start": s, "end": e, "sha256": json.loads(p.read_text())["npy_sha256"]}
                         for s, e, p, _ in pieces]}
        save_atomic(result, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode())
        return doc
    finally:
        if stage.exists():
            stage.unlink()


def run_shard(args):
    import torch
    from transformers import EsmModel, EsmTokenizer
    # Reuse validated scientific pooling routine, do not reimplement it.
    here = Path(__file__).resolve().parents[1] / "esm2_t33_pilot_20261102"
    if not (here / "run_t33_pilot.py").exists():
        # Running standalone from local test staging directory.
        here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from run_t33_pilot import extract

    torch.set_num_threads(2)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    data = read_dataset(Path(args.dataset))
    a, b = (args.start, args.end) if args.start is not None else shard_interval(args.rank, args.shards)
    if a is None or b is None or a < 0 or b > N or b <= a:
        raise ValueError("Invalid source range")
    model = EsmModel.from_pretrained(MODEL_ID, revision=MODEL_SHA, use_safetensors=True).eval().to("cpu")
    tok = EsmTokenizer.from_pretrained(MODEL_ID, revision=MODEL_SHA)
    print(f"START range={a}:{b} model={MODEL_ID}@{MODEL_SHA}", flush=True)
    done = 0
    with torch.inference_mode():
        for start in range(a, b, args.block_size):
            end = min(start + args.block_size, b)
            fp = Path(args.outdir) / f"part_{start:05d}_{end:05d}.json"
            if fp.exists():
                info, _ = verify_block(fp, expected_device="cpu")
                if info["start"] != start or info["end"] != end:
                    raise ValueError("Resume block range mismatch")
                print(f"RESUME_SKIP {start}:{end}", flush=True)
                done += end-start
                continue
            vectors = np.empty((end-start, D), dtype=np.float32)
            for j, index in enumerate(range(start, end)):
                seq = data[index]["sequence"]
                if not isinstance(seq, str) or not (1 <= len(seq) <= 1022):
                    raise ValueError(f"Invalid sequence at {index}")
                enc = tok(seq, return_tensors="pt", truncation=False, add_special_tokens=True)
                hid = model(**enc).last_hidden_state[0]
                vector, _ = extract(enc, hid, tok, len(seq))
                if vector.shape != (D,):
                    raise ValueError("Model dimension mismatch")
                if index in ANCHOR_HASHES:
                    digest = hashlib.sha256(vector.tobytes()).hexdigest()
                    if digest != ANCHOR_HASHES[index]:
                        raise ValueError(f"Previously validated anchor {index} differs: {digest}")
                vectors[j] = vector
            info = save_block(args.outdir, start, end, vectors, "cpu")
            done += end-start
            print(f"BLOCK {start}:{end} rows={done}/{b-a} sha256={info['npy_sha256']}", flush=True)
    print(f"DONE {a}:{b}", flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shard")
    s.add_argument("--dataset", default="data/sequences/proteins_25k_sequences.json")
    s.add_argument("--outdir", required=True)
    s.add_argument("--rank", type=int, default=0)
    s.add_argument("--shards", type=int, default=1)
    s.add_argument("--start", type=int, default=None)
    s.add_argument("--end", type=int, default=None)
    s.add_argument("--block-size", type=int, default=128)
    a = sub.add_parser("assemble")
    a.add_argument("--inputs", required=True)
    a.add_argument("--outdir", required=True)
    args = p.parse_args()
    if args.cmd == "shard":
        if args.block_size < 1 or args.block_size > 512:
            raise ValueError("Invalid block size")
        if (args.start is None) != (args.end is None):
            raise ValueError("Specify both --start and --end")
        run_shard(args)
    else:
        doc = assemble(args.inputs, args.outdir)
        print("ASSEMBLED=" + json.dumps({k: doc[k] for k in ("rows", "dim", "output_sha256")}))


if __name__ == "__main__":
    main()
