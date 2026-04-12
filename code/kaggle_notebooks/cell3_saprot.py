
# SaProt-650M-AF2: uses structural tokens, but we run on sequence-only mode
# to match the homology-cliff setup
tokenizer = AutoTokenizer.from_pretrained('westlake-repl/SaProt_650M_AF2')
model = AutoModel.from_pretrained('westlake-repl/SaProt_650M_AF2', trust_remote_code=True).to(device).eval()
embeddings = []
BATCH = 2; MAX_LEN = 1022
for i in range(0, len(seqs), BATCH):
    batch = seqs[i:i+BATCH]
    # Sequence-only: use #### for structure tokens
    batch_sa = [''.join(a + '#' for a in s[:MAX_LEN]) for s in batch]
    ids = tokenizer(batch_sa, padding=True, truncation=True, max_length=MAX_LEN*2, return_tensors='pt').to(device)
    with torch.no_grad():
        out = model(**ids).last_hidden_state
    mask = ids['attention_mask'].unsqueeze(-1).float()
    pooled = (out * mask).sum(1) / mask.sum(1)
    embeddings.append(pooled.cpu().numpy())
    if i % 500 == 0: print(f'  {i}/{len(seqs)}')
emb = np.concatenate(embeddings, axis=0).astype(np.float32)
emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
np.save('/kaggle/working/embeddings_saprot.npy', emb)
print('saprot done:', emb.shape)
