
# For each target, generate N candidate edits
AA = list('ACDEFGHIKLMNPQRSTVWY')

def blosum_score(a, b):
    return blosum62.get((a,b), blosum62.get((b,a), -99))

def top_edits(seq, n_edits=30):
    '''Generate BLOSUM-favorable single-residue substitutions.'''
    candidates = []
    for pos in range(len(seq)):
        orig = seq[pos]
        if orig not in AA: continue
        for repl in AA:
            if repl == orig: continue
            score = blosum_score(orig, repl)
            if score < 0: continue  # only BLOSUM-conservative edits
            new = seq[:pos] + repl + seq[pos+1:]
            candidates.append((score, pos, orig, repl, new))
    candidates.sort(key=lambda x: -x[0])
    return candidates[:n_edits]

results = {}
for acc, seq in seqs.items():
    print(f'\n{acc} ({len(seq)} aa)')
    edits = top_edits(seq, n_edits=30)
    edit_seqs = [e[4] for e in edits]
    # Embed original + edits in one batch
    all_embs = embed([seq] + edit_seqs)
    orig_emb = all_embs[0]
    edit_embs = all_embs[1:]
    # Save results
    results[acc] = {
        'original_sequence': seq,
        'original_embedding': orig_emb.tolist(),
        'edits': [
            {'blosum_score': int(e[0]), 'pos': int(e[1]), 'from_aa': e[2], 'to_aa': e[3],
             'embedding': edit_embs[i].tolist(),
             'cos_to_orig': float(edit_embs[i] @ orig_emb)}
            for i, e in enumerate(edits)
        ]
    }
    # Report closest-to-original and farthest
    coss = [e['cos_to_orig'] for e in results[acc]['edits']]
    print(f'  cos(edited, original): min={min(coss):.4f} max={max(coss):.4f} median={np.median(coss):.4f}')

with open('/kaggle/working/adversarial_edits.json', 'w') as f:
    json.dump({k: {'original_sequence': v['original_sequence'], 'edits': v['edits']} for k,v in results.items()}, f)
print('wrote adversarial_edits.json')
