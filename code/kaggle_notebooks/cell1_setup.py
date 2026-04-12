
!pip install -q transformers torch sentencepiece

import torch, numpy as np, json
from transformers import T5Tokenizer, T5EncoderModel, AutoTokenizer, AutoModel
device = 'cuda'

# Load proteins (upload the JSON as Kaggle dataset or fetch via UniProt)
# Assume dataset is at /kaggle/input/protein-test-set/experiment2_proteins_25k_filtered.json
with open('/kaggle/input/protein-test-set/experiment2_proteins_25k_filtered.json') as f:
    doc = json.load(f)
entries = doc['test_set']
seqs = [e['sequence'] for e in entries]
print(f'loaded {len(seqs)} sequences, max_len {max(len(s) for s in seqs)}')
