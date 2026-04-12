
# ProtT5-XL-UniRef50
tokenizer = T5Tokenizer.from_pretrained('Rostlab/prot_t5_xl_uniref50', do_lower_case=False)
model = T5EncoderModel.from_pretrained('Rostlab/prot_t5_xl_uniref50').to(device).eval()

embeddings = []
BATCH = 4; MAX_LEN = 1022
for i in range(0, len(seqs), BATCH):
    batch = seqs[i:i+BATCH]
    batch = [' '.join(list(s[:MAX_LEN])) for s in batch]
    ids = tokenizer(batch, padding=True, return_tensors='pt').to(device)
    with torch.no_grad():
        out = model(**ids).last_hidden_state  # (B, L, 1024)
    # Mean-pool over sequence length (excluding padding)
    mask = ids['attention_mask'].unsqueeze(-1).float()
    pooled = (out * mask).sum(1) / mask.sum(1)
    embeddings.append(pooled.cpu().numpy())
    if i % 500 == 0: print(f'  {i}/{len(seqs)}')
emb = np.concatenate(embeddings, axis=0).astype(np.float32)
emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
np.save('/kaggle/working/embeddings_prot_t5.npy', emb)
print('prot_t5 done:', emb.shape)
