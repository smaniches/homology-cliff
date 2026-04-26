"""scripts/build_summary_figure.py -- generate the v1.4.4 summary figure.

Reads only committed JSON / aggregate evidence (no LFS payload required)
and produces figures/cliff_summary.png, a 4-panel TL;DR of the entire
compendium:

    Panel A: cliff gap by panel size and scale (the headline phenomenon)
    Panel B: main vs full-null gap distributions (the cliff is real)
    Panel C: per-stratum Expected Calibration Error (precision collapse)
    Panel D: distant F1 by metric at t30 R=1000 k=25 (the rescue)

Sources:
    data/results_summaries/v3_final.txt        (UTF-16 LE; cliff + null + rescue)
    data/results_summaries/calibration_results.json (Paper 3 numbers)

Output:
    figures/cliff_summary.png

Repo-relative; runnable from any clone after `pip install matplotlib`.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(
    os.environ.get("HOMOLOGY_CLIFF_REPO_ROOT",
                   Path(__file__).resolve().parents[1])
)
V3 = REPO_ROOT / "data" / "results_summaries" / "v3_final.txt"
CAL = REPO_ROOT / "data" / "results_summaries" / "calibration_results.json"
OUT = REPO_ROOT / "figures" / "cliff_summary.png"


# ---------------------------------------------------------------------------
# Parse v3_final.txt (UTF-16 LE, fixed-width columns)
# ---------------------------------------------------------------------------

def read_v3() -> str:
    return V3.read_text(encoding="utf-16")


def parse_main_table(text: str) -> list[dict]:
    """MAIN gap table rows: scale R k metric close dist gap std up."""
    rows: list[dict] = []
    in_main = False
    for line in text.splitlines():
        if "=== MAIN gap table ===" in line:
            in_main = True; continue
        if in_main and line.startswith("==="):
            break
        if not in_main:
            continue
        m = re.match(
            r"\s*(t\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+"
            r"([\d.]+)\s+([\d.]+)\s+([\d.\-]+)\s+([\d.]+)\s+(\d+)",
            line)
        if not m:
            continue
        rows.append(dict(
            scale=m.group(1), R=int(m.group(2)), k=int(m.group(3)),
            metric=m.group(4),
            close=float(m.group(5)), distant=float(m.group(6)),
            gap=float(m.group(7)), std=float(m.group(8)),
            voided=int(m.group(9)),
        ))
    return rows


def parse_fullnull_table(text: str) -> list[dict]:
    """FULL-NULL table rows."""
    rows: list[dict] = []
    in_fn = False
    for line in text.splitlines():
        if "=== FULL-NULL" in line:
            in_fn = True; continue
        if in_fn and line.startswith("==="):
            break
        if not in_fn:
            continue
        m = re.match(
            r"\s*(t\d+)\s+(\d+)\s+(\d+)\s+(\w+)\s+"
            r"([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)",
            line)
        if not m:
            continue
        rows.append(dict(
            scale=m.group(1), R=int(m.group(2)), k=int(m.group(3)),
            metric=m.group(4),
            close=float(m.group(5)), moderate=float(m.group(6)),
            distant=float(m.group(7)), gap=float(m.group(8)),
        ))
    return rows


# ---------------------------------------------------------------------------
# Build figure
# ---------------------------------------------------------------------------

def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    text = read_v3()
    main_rows = parse_main_table(text)
    fn_rows = parse_fullnull_table(text)
    cal = json.loads(CAL.read_text(encoding="utf-8"))

    # ----- Panel A: cliff gap by panel size and scale (k=25 cosine) -----
    panel_sizes = [50, 100, 250, 500, 1000]
    by_scale = {"t6": [], "t12": [], "t30": []}
    for s in by_scale:
        for R in panel_sizes:
            row = next((r for r in main_rows
                       if r["scale"] == s and r["R"] == R
                       and r["k"] == 25 and r["metric"] == "cosine"), None)
            by_scale[s].append(row["gap"] if row else float("nan"))

    # ----- Panel B: gap histograms (main vs full-null) on the same subspace ---
    # Full-null was computed for (k in {1, 25}) x (metric in {cosine, mahalanobis})
    # = 3 scales x 5 R x 2 k x 2 metrics = 60 cells. We compare to the
    # corresponding 60 main cells for a like-for-like distribution.
    def _is_fn_subspace(r):
        return r["k"] in (1, 25) and r["metric"] in ("cosine", "mahalanobis")
    main_gaps = [r["gap"] for r in main_rows if _is_fn_subspace(r)]
    fn_gaps = [r["gap"] for r in fn_rows if _is_fn_subspace(r)]

    # ----- Panel C: per-stratum ECE -----
    ece = {s: cal[s]["ECE"] for s in ("close", "moderate", "distant")}

    # ----- Panel D: distant F1 by metric at t30 R=1000 k=25 -----
    metrics_d = ("cosine", "mahalanobis", "learned")
    distant_by_metric = {}
    close_by_metric = {}
    for met in metrics_d:
        row = next((r for r in main_rows
                   if r["scale"] == "t30" and r["R"] == 1000
                   and r["k"] == 25 and r["metric"] == met), None)
        distant_by_metric[met] = row["distant"] if row else float("nan")
        close_by_metric[met] = row["close"] if row else float("nan")

    # --- Figure layout ------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
    fig.suptitle(
        "The Homology Cliff in Frozen ESM-2 Biosecurity Retrieval  -  v1.4.4 summary",
        fontsize=13, fontweight="bold", y=0.995)

    # Panel A
    ax = axes[0, 0]
    colors = {"t6": "#1f77b4", "t12": "#ff7f0e", "t30": "#2ca02c"}
    labels = {"t6": "t6 (8M params)", "t12": "t12 (35M)", "t30": "t30 (150M)"}
    for s in ("t6", "t12", "t30"):
        ax.plot(panel_sizes, by_scale[s], "o-", color=colors[s],
                label=labels[s], linewidth=2, markersize=7)
    ax.set_xscale("log")
    ax.set_xticks(panel_sizes); ax.set_xticklabels([str(R) for R in panel_sizes])
    ax.set_xlabel("panel size R"); ax.set_ylabel("close $-$ distant $F_1$ gap")
    ax.set_title("(a) The cliff grows with model scale and panel size",
                 loc="left", fontsize=11)
    ax.set_ylim(0, 0.85)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    ax.text(0.02, 0.96, "k=25 cosine", transform=ax.transAxes,
            fontsize=9, alpha=0.7, va="top")

    # Panel B
    ax = axes[0, 1]
    bins = np.linspace(-0.2, 0.85, 35)
    ax.hist(fn_gaps, bins=bins, alpha=0.7, color="#d62728",
            label=f"full-null (n={len(fn_gaps)} groups)", edgecolor="white")
    ax.hist(main_gaps, bins=bins, alpha=0.7, color="#1f77b4",
            label=f"main factorial (n={len(main_gaps)} groups)",
            edgecolor="white")
    ax.axvline(0.0, color="black", linewidth=0.8, linestyle="--")
    ax.set_xlabel("close $-$ distant $F_1$ gap")
    ax.set_ylabel("group count")
    ax.set_title("(b) Full-pool null gaps cluster at zero; main gaps do not",
                 loc="left", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.text(0.02, 0.96,
            "k$\\in\\{$1,25$\\}$ x metric$\\in\\{$cosine,Mahalanobis$\\}$, 10-seed mean per cell",
            transform=ax.transAxes, fontsize=9, alpha=0.7, va="top")

    # Panel C
    ax = axes[1, 0]
    strata = ["close", "moderate", "distant"]
    eces = [ece[s] for s in strata]
    bar_colors = ["#1f77b4", "#ff7f0e", "#d62728"]
    bars = ax.bar(strata, eces, color=bar_colors, edgecolor="black",
                  linewidth=0.8)
    for bar, e in zip(bars, eces):
        ax.text(bar.get_x() + bar.get_width() / 2, e + 0.008,
                f"{e:.3f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_ylabel("Expected Calibration Error (ECE)")
    ax.set_title("(c) Calibration collapses on the distant stratum",
                 loc="left", fontsize=11)
    ax.set_ylim(0, max(eces) * 1.25)
    ax.grid(True, alpha=0.3, axis="y")
    ratio = ece["distant"] / ece["close"]
    ax.text(0.5, 0.85,
            f"distant / close = {ratio:.1f}$\\times$\n"
            f"distant pos-pred precision = "
            f"{cal['distant']['positive_prediction']['tp']}/"
            f"{cal['distant']['positive_prediction']['n_predicted_positive']} "
            f"= {cal['distant']['positive_prediction']['precision']:.3f}",
            transform=ax.transAxes, fontsize=9, ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="grey", alpha=0.85))
    ax.text(0.02, 0.96, "t30 R=1000 k=25 cosine, seed 20260410",
            transform=ax.transAxes, fontsize=9, alpha=0.7, va="top")

    # Panel D
    ax = axes[1, 1]
    x = np.arange(len(metrics_d))
    width = 0.35
    closes = [close_by_metric[m] for m in metrics_d]
    distants = [distant_by_metric[m] for m in metrics_d]
    b1 = ax.bar(x - width/2, closes, width, color="#1f77b4",
                label="close stratum", edgecolor="black", linewidth=0.8)
    b2 = ax.bar(x + width/2, distants, width, color="#d62728",
                label="distant stratum", edgecolor="black", linewidth=0.8)
    for bar, v in zip(b1, closes):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.012,
                f"{v:.2f}", ha="center", fontsize=9)
    for bar, v in zip(b2, distants):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.012,
                f"{v:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(
        ["cosine\n(baseline)", "Mahalanobis\n(rescue 1: rejected)",
         "learned\n(rescue 5: accepted)"], fontsize=9)
    ax.set_ylabel("$F_1$")
    ax.set_title("(d) Of five rescues, only learned projection helps distant",
                 loc="left", fontsize=11)
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend(loc="upper right", fontsize=9)
    rescue = distant_by_metric["learned"] / distant_by_metric["cosine"] - 1.0
    ax.text(0.02, 0.96,
            f"t30 R=1000 k=25  -  learned: +{rescue*100:.0f}% relative distant $F_1$",
            transform=ax.transAxes, fontsize=9, alpha=0.7, va="top")

    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.text(0.5, 0.005,
             "github.com/smaniches/homology-cliff  -  9,360 pre-registered cells "
             "-  4 SHA256-locked pre-registrations  -  CC-BY-4.0 papers / MIT code",
             ha="center", fontsize=8.5, style="italic", color="#444")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"wrote {OUT}  ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
