"""C2: decomposition of the gap between policies and the best achievable cost.

Reads the frozen results (no new simulation):
  outputs/stream_eval.jsonl       continuous streams, test pool, S and M (60 streams)
  outputs/stream_hindsight.jsonl  finite S instances, hindsight pool (n = 6: 30, n = 10: 12)

Ladders (every rung is a paired per-instance ratio to one reference, so the
steps between rungs add up exactly to the total gap):

  Continuous, reference FCFS-VAA (relative J/work, %)
    static framework   Cyclic-CPSAT  -> FCFS-VAA   (cycle-optimal static plans vs a state-based rule)
    rule tuning        FCFS-VAA      -> Tuned-Rule
    learned policy     Tuned-Rule    -> RL-API     (non-linear judgement, same information)
    distillation       RL-API        -> Rollout    (what the fast network leaves on the table)
    information        Rollout       -> Rollout-Oracle (knowing the real future)
  Finite, reference HS-event (best perfect-information schedule in the policy action space)
    look-ahead         FCFS-VAA      -> Rollout
    information        Rollout       -> Rollout-Oracle
    optimization       Rollout-Oracle -> HS-event  (one-step improvement vs full optimization)
  plus the HS-event vs HS-free check on instances where both are proven optimal.

Steps get paired bootstrap 95% CIs (10,000 resamples of instances) and a
Wilcoxon signed-rank p (scipy).

Writes outputs/stream_gap_decomposition.txt and paper/figures/stream_gap_decomposition.{pdf,png}.

Usage:
    python experiments/stream_gap_decomposition.py
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "outputs" / "stream_eval.jsonl"
HINDSIGHT = ROOT / "outputs" / "stream_hindsight.jsonl"
TEXT = ROOT / "outputs" / "stream_gap_decomposition.txt"
FIGURE = ROOT / "paper" / "figures" / "stream_gap_decomposition"

STREAM_LADDER = ["Cyclic-CPSAT", "FCFS-VAA", "Tuned-Rule", "RL-API", "Rollout", "Rollout-Oracle"]
STREAM_STEPS = ["static framework", "rule tuning", "learned policy", "distillation", "information"]
FINITE_LADDER = ["FCFS-VAA", "Tuned-Rule", "RL-API", "Rollout", "Rollout-Oracle", "HS-event"]
FINITE_STEPS = [("FCFS-VAA", "Rollout", "look-ahead"), ("Rollout", "Rollout-Oracle", "information"),
                ("Rollout-Oracle", "HS-event", "optimization")]
BOOT = 10_000


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    idx = rng.integers(0, len(values), size=(BOOT, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def wilcoxon_p(values: np.ndarray) -> float:
    from scipy.stats import wilcoxon

    return float(wilcoxon(values).pvalue) if np.any(values != 0) else 1.0


def stream_table() -> dict[str, np.ndarray]:
    """Per-stream J/work ratio to FCFS-VAA minus 1, S and M test streams."""

    by: dict[tuple, dict[str, float]] = defaultdict(dict)
    for line in EVAL.read_text().splitlines():
        r = json.loads(line)
        if r["size"] in ("S", "M") and r["method"] in STREAM_LADDER:
            by[(r["size"], r["load"], r["demand"], r["rep"])][r["method"]] = r["objective"] / r["mean_work"]
    keys = sorted(k for k, v in by.items() if all(m in v for m in STREAM_LADDER))
    rel = {m: np.array([by[k][m] / by[k]["FCFS-VAA"] - 1 for k in keys]) for m in STREAM_LADDER}
    rel["_keys"] = keys  # type: ignore[assignment]
    return rel


def finite_table(n: int) -> dict[str, np.ndarray]:
    """Per-instance ratio to HS-event minus 1."""

    rows = [json.loads(line) for line in HINDSIGHT.read_text().splitlines()]
    rows = [r for r in rows if r["n"] == n]
    ref = np.array([r["hs_event"]["objective"] for r in rows])
    rel = {m: np.array([r["policies"][m]["objective"] for r in rows]) / ref - 1 for m in FINITE_LADDER[:-1]}
    rel["HS-event"] = np.zeros(len(rows))
    rel["_rows"] = rows  # type: ignore[assignment]
    return rel


def step_line(name: str, worse: np.ndarray, better: np.ndarray, rng) -> tuple[str, float]:
    diff = worse - better  # positive = the step closes gap (in % of the reference)
    lo, hi = bootstrap_ci(diff, rng)
    line = (f"  {name:18} {100 * diff.mean():+7.1f} pp  [95% CI {100 * lo:+.1f}, {100 * hi:+.1f}]  "
            f"closes gap in {int(np.sum(diff > 0))}/{len(diff)}  Wilcoxon p = {wilcoxon_p(diff):.2g}")
    return line, float(diff.mean())


def summarize() -> tuple[str, dict]:
    rng = np.random.default_rng(0)
    out: list[str] = ["C2 gap decomposition (paired per-instance ratios; steps add up to the total)", ""]
    figure: dict = {}

    rel = stream_table()
    keys = rel.pop("_keys")
    out.append(f"A. Continuous streams, test pool S+M ({len(keys)} streams), gap to FCFS-VAA in % of FCFS-VAA J/work")
    for m in STREAM_LADDER:
        lo, hi = bootstrap_ci(rel[m], rng)
        out.append(f"  {m:16} {100 * rel[m].mean():+7.1f}%  [95% CI {100 * lo:+.1f}, {100 * hi:+.1f}]")
    out.append("  steps")
    steps = []
    for (a, b), name in zip(zip(STREAM_LADDER, STREAM_LADDER[1:]), STREAM_STEPS):
        line, value = step_line(name, rel[a], rel[b], rng)
        out.append(line)
        steps.append((name, value))
    figure["stream"] = {"ladder": [(m, float(rel[m].mean())) for m in STREAM_LADDER], "steps": steps,
                        "ci": [bootstrap_ci(rel[m], rng) for m in STREAM_LADDER]}
    for size in ("S", "M"):
        mask = np.array([k[0] == size for k in keys])
        parts = " ".join(f"{m}={100 * rel[m][mask].mean():+.1f}" for m in STREAM_LADDER)
        out.append(f"  {size}: {parts}")
    for load in (0.5, 0.6, 0.7):
        mask = np.array([k[1] == load for k in keys])
        parts = " ".join(f"{m}={100 * rel[m][mask].mean():+.1f}" for m in STREAM_LADDER)
        out.append(f"  load {load}: {parts}")
    out.append("")

    figure["finite"] = {}
    for n in (6, 10):
        rel = finite_table(n)
        rows = rel.pop("_rows")
        proved = sum(r["hs_event"]["optimal"] for r in rows)
        out.append(f"B. Finite S instances, n = {n} trucks ({len(rows)} instances, HS-event proven optimal in {proved}), "
                   f"gap to HS-event in % of HS-event")
        for m in FINITE_LADDER:
            lo, hi = bootstrap_ci(rel[m], rng)
            out.append(f"  {m:16} {100 * rel[m].mean():+7.1f}%  [95% CI {100 * lo:+.1f}, {100 * hi:+.1f}]")
        out.append("  steps")
        steps = []
        for a, b, name in FINITE_STEPS:
            line, value = step_line(name, rel[a], rel[b], rng)
            out.append(line)
            steps.append((name, value))
        total = float(rel["Rollout"].mean())
        info = steps[1][1]
        out.append(f"  Rollout's gap {100 * total:+.1f}%: information {100 * info:.1f} pp ({info / total:.0%}), "
                   f"optimization {100 * steps[2][1]:.1f} pp ({steps[2][1] / total:.0%})")
        both = [r for r in rows if r["hs_event"]["optimal"] and r["hs_free"]["optimal"]]
        if both:
            gap = np.array([r["hs_event"]["objective"] / r["hs_free"]["objective"] - 1 for r in both])
            out.append(f"  action-space check: HS-event vs proven free-timing optimum on {len(both)} instances "
                       f"{100 * gap.mean():+.2f}% (max {100 * gap.max():+.2f}%) -> HS-event is a near-exact optimum")
        else:
            out.append("  action-space check: no instance with both models proven optimal; HS-event is the best schedule "
                       "found, so the true optimization gap may be larger")
        figure["finite"][n] = {"ladder": [(m, float(rel[m].mean())) for m in FINITE_LADDER], "steps": steps,
                               "ci": [bootstrap_ci(rel[m], rng) for m in FINITE_LADDER],
                               "count": len(rows), "proved": proved}
        out.append("")

    out += [
        "Reading",
        "  - The static framework is the largest single loss; solving the cycles optimally does not remove it.",
        "  - Look-ahead closes about half of the rule's gap to the hindsight optimum (46% at n = 6, 58% at n = 10).",
        "  - Of what remains for Rollout, information explains about 0% (n = 6) to 41% (n = 10); the rest is an optimization gap that",
        "    neither more samples (Rollout-32), a better base policy (Rollout@api) nor hindsight teachers closed.",
    ]
    return "\n".join(out), figure


def plot(figure: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#1a1a1a", "#6b6b6b", "#d9d9d9"
    # journal palette (paper figures): blue = policies, teal = look-ahead family, purple = references
    blue, teal, purple = "#2b6cb0", "#2e9a86", "#8a63a8"
    family = {"Cyclic-CPSAT": purple, "FCFS-VAA": blue, "Tuned-Rule": blue, "RL-API": blue,
              "Rollout": teal, "Rollout-Oracle": teal, "HS-event": purple}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": muted,
                         "axes.labelcolor": ink, "xtick.color": muted, "ytick.color": ink})
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.25, 1, 1]})

    def ladder(ax, data, title, xlabel):
        names = [m for m, _ in data["ladder"]]
        values = np.array([100 * v for _, v in data["ladder"]])
        ci = 100 * np.array(data["ci"])
        y = np.arange(len(names))[::-1]
        ax.barh(y, values, height=0.55, color=[family[m] for m in names], zorder=2)
        err = np.vstack([values - ci[:, 0], ci[:, 1] - values])
        ax.errorbar(values, y, xerr=err, fmt="none", ecolor=ink, elinewidth=0.7, capsize=2, zorder=3)
        ax.axvline(0, color=muted, lw=0.8, zorder=1)
        ax.set_yticks(y, names)
        ax.xaxis.grid(True, color=grid, lw=0.6, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.set_title(title, fontsize=8.5, color=ink, loc="left")
        ax.set_xlabel(xlabel)
        lo, hi = min(ci[:, 0].min(), 0), max(ci[:, 1].max(), 0)
        span = hi - lo
        for yy, v, (c_lo, c_hi) in zip(y, values, ci):
            # label beyond the whisker, on the bar's side; zero rungs labelled just right of the axis
            if v > 0:
                ax.text(c_hi + 0.03 * span, yy, f"{v:+.1f}", va="center", ha="left", fontsize=7, color=ink)
            elif v < 0:
                ax.text(c_lo - 0.03 * span, yy, f"{v:+.1f}", va="center", ha="right", fontsize=7, color=ink)
            else:
                ax.text(0.03 * span, yy, "0 (ref.)", va="center", ha="left", fontsize=7, color=muted)
        ax.set_xlim(lo - (0.32 * span if lo < 0 else 0.05 * span), hi + 0.22 * span)
        return ax

    s = figure["stream"]
    ladder(axes[0], s, "(a) Continuous, S+M (60)", "gap to FCFS-VAA (%)")
    for ax, n in zip(axes[1:], (6, 10)):
        f = figure["finite"][n]
        ladder(ax, f, f"({'b' if n == 6 else 'c'}) Finite S, n={n} ({f['count']})", "gap to HS-event (%)")
    from matplotlib.patches import Patch

    fig.legend(handles=[Patch(color=blue, label="rule / learned policy"), Patch(color=teal, label="look-ahead (Rollout)"),
                        Patch(color=purple, label="static cycle optimum (a) / hindsight optimum (b, c)")],
               loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(w_pad=1.2, rect=(0, 0.07, 1, 1))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE.with_suffix(".pdf"))
    fig.savefig(FIGURE.with_suffix(".png"), dpi=220)
    plt.close(fig)


def main() -> None:
    text, figure = summarize()
    TEXT.write_text(text + "\n")
    print(text)
    plot(figure)


if __name__ == "__main__":
    main()
