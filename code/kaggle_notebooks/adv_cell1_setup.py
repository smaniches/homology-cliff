
!pip install -q transformers torch biopython
import torch, numpy as np, json, urllib.request
from transformers import EsmTokenizer, EsmModel
from Bio.SubsMat.MatrixInfo import blosum62
device = 'cuda'

# Fetch 3 target sequences from UniProt
TARGETS = ['P0C1X3', 'Q6RY98', 'P13208']
seqs = {}
for acc in TARGETS:
    url = f'https://www.uniprot.org/uniprot/{acc}.fasta'
    txt = urllib.request.urlopen(url).read().decode()
    seq = ''.join(txt.split('\n')[1:])
    seqs[acc] = seq
    print(f'{acc}: len {len(seq)}')

tokenizer = EsmTokenizer.from_pretrained('facebook/esm2_t30_150M_UR50D')
model = EsmModel.from_pretrained('facebook/esm2_t30_150M_UR50D').to(device).eval()

def embed(sequences):
    encoded = tokenizer(sequences, padding=True, truncation=True, max_length=1022, return_tensors='pt').to(device)
    with torch.no_grad():
        out = model(**encoded).last_hidden_state
    mask = encoded['attention_mask'].unsqueeze(-1).float()
    pooled = (out * mask).sum(1) / mask.sum(1)
    emb = pooled.cpu().numpy().astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
    return emb
