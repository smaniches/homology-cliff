#!/usr/bin/env python3
"""Read-only exploratory compatibility assay for frozen ESM-2 t30 embeddings.

This is not a scientific validation of the original labels or a published benchmark.
The assay compares four operationally different pooling/truncation conventions.
"""
import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path

import numpy as np

DATASET = Path('data/sequences/proteins_25k_sequences.json')
REFERENCE = Path('data/embeddings/embeddings_t30.npy')
DATASET_SHA = 'c99d8329c02b806b9d208465946c68826d17245cd9e012ca9a7b94faea0a60fc'
REFERENCE_SHA = '15d6e3656b46729a2483b7fbc603e49a61f25206e3854676bc2e528164608fd6'
MODEL = 'facebook/esm2_t30_150M_UR50D'


def verify(path, expected):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(4 * 1024 * 1024), b''):
            digest.update(part)
    actual = digest.hexdigest()
    if actual != expected:
        raise RuntimeError(f'file hash mismatch: {path}: {actual} != {expected}')
    return actual


def pick_indices(rows):
    """Prespecified length stratification plus two edge cases, independent of results."""
    lengths = np.array([len(row['sequence']) for row in rows], dtype=np.int32)
    rng = np.random.default_rng(20261101)
    boundaries = [0, 100, 350, 700, 1021, 10**10]
    selected = {int(lengths.argmin()), int(lengths.argmax())}
    for low, high in zip(boundaries[:-1], boundaries[1:]):
        eligible = np.flatnonzero((lengths >= low) & (lengths < high))
        if len(eligible):
            n = min(4, len(eligible))
            chosen = rng.choice(eligible, size=n, replace=False)
            selected.update(map(int, chosen))
    return sorted(selected)


def l2(vec):
    v = np.asarray(vec, dtype=np.float64)
    norm = float(np.linalg.norm(v))
    if not np.isfinite(norm) or norm < 1e-9:
        raise ValueError('invalid norm')
    return v / norm


def normalized_cos(a,b):
    return float(np.dot(l2(a), l2(b)))


def main():
    import torch
    from transformers import EsmTokenizer, EsmModel
    from huggingface_hub import HfApi
    torch.set_num_threads(2)
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    verify(DATASET, DATASET_SHA)
    verify(REFERENCE, REFERENCE_SHA)
    record = json.loads(DATASET.read_text())
    rows = record['test_set']
    if len(rows) != 24885 or not all(isinstance(x.get('sequence'),str) and x['sequence'] for x in rows):
        raise ValueError('unexpected data schema or row count')
    arr = np.load(REFERENCE, mmap_mode='r', allow_pickle=False)
    if arr.shape != (len(rows),640) or arr.dtype.kind!='f':
        raise ValueError(f'unexpected reference: {arr.shape} {arr.dtype}')
    if not np.isfinite(arr).all(): raise ValueError('non-finite reference')
    chosen = pick_indices(rows)
    # Freeze the model revision before any forward pass; record it in the output.
    revision = HfApi().model_info(MODEL).sha
    if not isinstance(revision,str) or len(revision)!=40:
        raise RuntimeError('could not resolve immutable model revision')
    tokenizer=EsmTokenizer.from_pretrained(MODEL,revision=revision)
    model=EsmModel.from_pretrained(MODEL,revision=revision,use_safetensors=True).eval()
    options=['residue_1022:legacy_attention','residue_1022:residue_only',
             'token_window_1022:legacy_attention','token_window_1022:residue_only']
    sims={key:[] for key in options}
    lengths={}
    with torch.inference_mode():
        for index in chosen:
            seq=rows[index]['sequence']
            lengths[str(index)]=len(seq)
            ref=arr[index].astype(np.float64)
            for truncation in ('residue_1022','token_window_1022'):
                if truncation=='residue_1022':
                    encoded=tokenizer(seq[:1022],return_tensors='pt',add_special_tokens=True, truncation=False)
                else:
                    encoded=tokenizer(seq,return_tensors='pt',add_special_tokens=True, truncation=True,max_length=1022)
                hidden=model(**encoded).last_hidden_state[0]
                att=encoded['attention_mask'][0].bool()
                ids=encoded['input_ids'][0]
                residue=att & (ids!=tokenizer.cls_token_id) & (ids!=tokenizer.eos_token_id) & (ids!=tokenizer.pad_token_id)
                if int(residue.sum())<=0:raise ValueError('empty residue set')
                for label,mask in [('legacy_attention',att),('residue_only',residue)]:
                    pooled=hidden[mask].float().mean(dim=0).numpy()
                    sim=normalized_cos(pooled,ref)
                    sims[f'{truncation}:{label}'].append(sim)
            print(f'PROGRESS {len(sims[options[0]])}/{len(chosen)} row={index} length={len(seq)}',flush=True)
    report={'status':'EXPLORATORY_COMPATIBILITY_ONLY', 'model':MODEL,'model_revision':revision,
        'input_sha256':DATASET_SHA,'reference_sha256':REFERENCE_SHA,
        'repo_revision':os.environ.get('GITHUB_SHA'),'numpy_version':np.__version__,
        'torch_version':torch.__version__,'transformers_version':importlib.metadata.version('transformers'),
        'python':platform.python_version(), 'indices':chosen,'lengths':lengths,'n':len(chosen),
        'options':{o:{'mean_cos':float(np.mean(v)),'min_cos':float(np.min(v)),
          'max_cos':float(np.max(v)),'cosines':[float(x) for x in v]} for o,v in sims.items()},
        'decision':'UNRESOLVED_REQUIRES_REVIEW',
        'limits':['selected deterministic length strata only','floating point/model conversion may differ from historical extraction','no change to historical data or results']}
    Path('parity_result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PARITY_SUMMARY='+json.dumps({o:{k:v for k,v in d.items() if k!='cosines'} for o,d in report['options'].items()},sort_keys=True),flush=True)


if __name__=='__main__':
    main()
