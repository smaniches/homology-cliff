
!pip install -q transformers torch sentencepiece

import torch, numpy as np, json
from transformers import T5Tokenizer, T5EncoderModel, AutoTokenizer, AutoModel
device = 'cuda'

# Load proteins. Upload data/sequences/proteins_25k_sequences.json from the
# repo as a Kaggle dataset attached to this notebook. The file is also known
# by its pre-registered working ID experiment2_proteins_25k_filtered.json;
# the loader accepts either name.
import os
_candidates = [
    '/kaggle/input/protein-test-set/proteins_25k_sequences.json',
    '/kaggle/input/protein-test-set/experiment2_proteins_25k_filtered.json',
]
_path = next((p for p in _candidates if os.path.exists(p)), _candidates[0])
with open(_path) as f:
    doc = json.load(f)
entries = doc['test_set']
seqs = [e['sequence'] for e in entries]
print(f'loaded {len(seqs)} sequences, max_len {max(len(s) for s in seqs)}')
