
# Final analysis (run locally after downloading adversarial_edits.json):
# 1. For each edit, compute s_max against the main panel
# 2. Check if s_max crosses 0.95 (close stratum)
# 3. Check if cosine k=25 vote flips from 0 (original) to 1 (edited)
# 4. Report minimum number of BLOSUM-favorable edits needed to flip each target
print('Download adversarial_edits.json and run locally:')
print('  python run_adversarial_phase2_local.py adversarial_edits.json')
