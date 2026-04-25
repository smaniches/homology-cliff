import numpy as np, glob, os, re, random
from collections import defaultdict
from pathlib import Path

random.seed(20260412)
REPO_ROOT = Path(__file__).resolve().parents[2]
CELLS_DIR = REPO_ROOT / "data" / "cells"
PAT = re.compile(r"(cell|negctrl|fullnull)_(t\d+)_(\d+)_(\d+)_(\w+?)_(\d+)\.npz$")

groups_main = defaultdict(list)
groups_neg  = defaultdict(list)
groups_full = defaultdict(list)
_npz_paths = (
    sorted(glob.glob(str(CELLS_DIR / "main" / "*.npz")))
    + sorted(glob.glob(str(CELLS_DIR / "negctrl" / "*.npz")))
    + sorted(glob.glob(str(CELLS_DIR / "fullnull" / "*.npz")))
)
for f in _npz_paths:
    m = PAT.search(f)
    if not m: continue
    kind, scale, r, k, metric, seed = m.group(1), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5), int(m.group(6))
    d = np.load(f, allow_pickle=True)
    c = d['close'].item(); mo = d['moderate'].item(); di = d['distant'].item()
    row = dict(cf=c['f1'], mf=mo['f1'], df=di['f1'], nc=c['n'], nm=mo['n'], nd=di['n'],
               up=(c['underpowered'] or mo['underpowered'] or di['underpowered']))
    if kind == 'fullnull':
        groups_full[(scale, r, k, metric)].append(row)
    elif kind == 'negctrl':
        groups_neg[(scale, r, k, metric)].append(row)
    else:
        groups_main[(scale, r, k, metric)].append(row)

print(f"main groups: {len(groups_main)}  cells: {sum(len(v) for v in groups_main.values())}")
print(f"negctrl groups: {len(groups_neg)}  cells: {sum(len(v) for v in groups_neg.values())}")
print(f"fullnull groups: {len(groups_full)}  cells: {sum(len(v) for v in groups_full.values())}")

# Full-null table: the real pre-reg-compliant null
print("\n=== FULL-NULL close/moderate/distant F1 (labels fully randomized) ===")
print("   Should ALL be near 0.5 per addendum pre-reg if cliff is real.")
print(f"{'scale':<4} {'R':>5} {'k':>3} {'metric':<12} {'close':>7} {'mod':>7} {'dist':>7} {'gap':>7} {'gap_std':>7}")
for scale in ['t6','t12','t30']:
    for r in [50,100,250,500,1000]:
        for k in [1,25]:
            for metric in ['cosine','mahalanobis']:
                g = groups_full.get((scale,r,k,metric),[])
                if len(g)<1: continue
                cf=np.mean([x['cf'] for x in g]); mf=np.mean([x['mf'] for x in g]); df=np.mean([x['df'] for x in g])
                gaps=[x['cf']-x['df'] for x in g]
                gstd = np.std(gaps, ddof=1) if len(gaps)>1 else 0.0
                n = len(g)
                print(f"{scale:<4} {r:>5} {k:>3} {metric:<12} {cf:>7.4f} {mf:>7.4f} {df:>7.4f} {cf-df:>7.4f} {gstd:>7.4f}  n={n}")

print("\n=== stratum n per seed, cosine ===")
for scale in ['t6','t12','t30']:
    for r in [50,1000]:
        g = groups_main.get((scale,r,25,'cosine'),[])
        if g:
            nd=[x['nd'] for x in g]; nm=[x['nm'] for x in g]; nc=[x['nc'] for x in g]
            print(f"  {scale} R={r}: n_close {min(nc)}-{max(nc)}  n_mod {min(nm)}-{max(nm)}  n_dist {min(nd)}-{max(nd)}")

print("\n=== MAIN gap table ===")
print(f"{'scale':<4} {'R':>5} {'k':>3} {'metric':<12} {'close':>7} {'dist':>7} {'gap':>7} {'std':>6} {'up':>3}")
for scale in ['t6','t12','t30']:
    for r in [50,100,250,500,1000]:
        for k in [1,3,5,10,25]:
            for metric in ['cosine','euclidean','learned','mahalanobis']:
                g = groups_main.get((scale,r,k,metric),[])
                if len(g)!=10: continue
                cf=np.mean([x['cf'] for x in g]); df=np.mean([x['df'] for x in g])
                gaps=[x['cf']-x['df'] for x in g]
                print(f"{scale:<4} {r:>5} {k:>3} {metric:<12} {cf:>7.4f} {df:>7.4f} {cf-df:>7.4f} {np.std(gaps,ddof=1):>6.4f} {sum(x['up'] for x in g):>3}")

print("\n=== NEGATIVE CONTROL gaps (should be near 0) ===")
print(f"{'scale':<4} {'R':>5} {'k':>3} {'metric':<12} {'neg_gap':>8} {'neg_std':>7} {'main_gap':>8}")
for scale in ['t6','t12','t30']:
    for r in [50,100,250,500,1000]:
        for k in [1,25]:
            for metric in ['cosine','mahalanobis']:
                gn = groups_neg.get((scale,r,k,metric),[])
                gm = groups_main.get((scale,r,k,metric),[])
                if len(gn)!=10 or len(gm)!=10: continue
                ng=[x['cf']-x['df'] for x in gn]; mg=[x['cf']-x['df'] for x in gm]
                print(f"{scale:<4} {r:>5} {k:>3} {metric:<12} {np.mean(ng):>+8.4f} {np.std(ng,ddof=1):>7.4f} {np.mean(mg):>+8.4f}")

print("\n=== cos vs mahalanobis reduction 95% CI at R=1000 k=25 ===")
B=5000
for scale in ['t6','t12','t30']:
    gc=groups_main[(scale,1000,25,'cosine')]; gm=groups_main[(scale,1000,25,'mahalanobis')]
    cg=[x['cf']-x['df'] for x in gc]; mg=[x['cf']-x['df'] for x in gm]
    diffs=[np.mean([random.choice(cg) for _ in range(10)])-np.mean([random.choice(mg) for _ in range(10)]) for _ in range(B)]
    diffs.sort()
    print(f"  {scale}: cos={np.mean(cg):.4f} mah={np.mean(mg):.4f} reduction={np.mean(cg)-np.mean(mg):+.4f} 95%CI=[{diffs[int(0.025*B)]:+.4f},{diffs[int(0.975*B)]:+.4f}]")

print("\n=== MODERATE-DISTANT second cliff at R=1000 k=25 ===")
for scale in ['t6','t12','t30']:
    for metric in ['cosine','mahalanobis']:
        g = groups_main[(scale,1000,25,metric)]
        cf=np.mean([x['cf'] for x in g]); mf=np.mean([x['mf'] for x in g]); df=np.mean([x['df'] for x in g])
        print(f"  {scale} {metric:<12}: close={cf:.4f} mod={mf:.4f} dist={df:.4f}  close-mod={cf-mf:.4f}  mod-dist={mf-df:.4f}")

print("\n=== DONE ===")
