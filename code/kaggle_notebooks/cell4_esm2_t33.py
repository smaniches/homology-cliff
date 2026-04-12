
# ESM-2 t33 650M -- completes the ESM-2 scaling ladder (t6, t12, t30, t33)
from transformers import EsmTokenizer, EsmModel
tokenizer = EsmTokenizer.from_pretrained('facebook/esm2_t33_650M_UR50D')
model = EsmModel.from_pretrained('facebook/esm2_t33_650M_UR50D').to(device).eval()
embeddings = []
BATCH = 2; MAX_LEN = 1022
for i in range(0, len(seqs), BATCH):
    batch = seqs[i:i+BATCH]
    batch = [s[:MAX_LEN] for s in batch]
    ids = tokenizer(batch, padding=True, return_tensors='pt').to(device)
    with torch.no_grad():
        out = model(**ids).last_hidden_state
    mask = ids['attention_mask'].unsqueeze(-1).float()
    pooled = (out * mask).sum(1) / mask.sum(1)
    embeddings.append(pooled.cpu().numpy())
    if i % 500 == 0: print(f'  {i}/{len(seqs)}')
emb = np.concatenate(embeddings, axis=0).astype(np.float32)
emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
np.save('/kaggle/working/embeddings_t33.npy', emb)
print('t33 done:', emb.shape)
