"""Summary of the (rho, delta) factorial experiment (reviewer comment R1-13).

For every size and (rho, delta) cell, over 20 instances (5 replications each):
  - GILS-uniform: mean makespan, mean total tardiness, mean objective
  - gain of GILS-uniform over VAA and over Extended SA-RL5
      gain% = 100 * (objective_other - objective_GILS) / objective_GILS  (positive = GILS better)
    with a paired two-sided Wilcoxon test on per-instance replication means.
Then the marginal (main-effect) means of each factor and paired tests between
the extreme levels of a factor (per-instance average over the other factor).

Usage:
    python experiments/tw_factorial_summary.py
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.k1_stats import wilcoxon_signed_rank

RESULTS = ROOT / "outputs" / "tw_factorial.jsonl"
SIZES = ("S", "M", "L")
RHOS = (0.0, 0.10, 0.25, 0.50)
DELTAS = (float("inf"), 1.00, 0.60, 0.35)
GILS, SA, VAA = "v2-GILS-uniform-1000", "Extended-SA-RL5-1000", "VAA"
mean = statistics.mean


def load():
    runs = defaultdict(list)
    for line in RESULTS.read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            runs[(r["method"], r["size_class"], r["rho"], r["delta"], r["index"])].append(r)
    return runs


def inst(runs, method, size, rho, delta, field):
    """Per-instance replication mean of a field, as {index: value}."""
    out = {}
    for (m, s, r, d, index), records in runs.items():
        if (m, s, r, d) == (method, size, rho, delta):
            out[index] = mean(rec[field] for rec in records)
    return out


def gains(runs, other, size, rho, delta):
    g = inst(runs, GILS, size, rho, delta, "objective")
    o = inst(runs, other, size, rho, delta, "objective")
    return {i: 100.0 * (o[i] - g[i]) / g[i] for i in g if i in o}


def main() -> None:
    runs = load()
    counts = defaultdict(int)
    for (m, *_), records in runs.items():
        counts[m] += len(records)
    print("runs per method:", dict(counts))

    for size in SIZES:
        print()
        print(f"=== Size {size}: GILS-uniform results and gains by (rho, delta), 20 instances ===")
        print(f"{'rho':>5}{'delta':>6}{'Cmax':>9}{'tard.':>10}{'obj.':>10}{'tard.share%':>12}"
              f"{'vs VAA%':>9}{'vs SA%':>8}{'p(SA)':>8}{'GILS<SA':>8}")
        for rho in RHOS:
            for delta in DELTAS:
                ms = mean(inst(runs, GILS, size, rho, delta, "makespan").values())
                td = mean(inst(runs, GILS, size, rho, delta, "total_tardiness").values())
                ob = mean(inst(runs, GILS, size, rho, delta, "objective").values())
                gv = gains(runs, VAA, size, rho, delta)
                gs = gains(runs, SA, size, rho, delta)
                p, _ = wilcoxon_signed_rank(list(gs.values()))
                wins = sum(v > 1e-12 for v in gs.values())
                print(f"{rho:>5.2f}{delta:>6.2f}{ms:>9.1f}{td:>10.1f}{ob:>10.1f}{100 * td / ob:>12.1f}"
                      f"{mean(gv.values()):>+9.2f}{mean(gs.values()):>+8.2f}{p:>8.4f}{wins:>5}/20")

    print()
    print("=== Main effects (marginal means over the other factor and all sizes) ===")
    for label, levels, pick in (("rho", RHOS, 0), ("delta", DELTAS, 1)):
        print(f"{label:>6}{'Cmax/H':>9}{'tard./H':>9}{'vs VAA%':>9}{'vs SA%':>8}")
        for level in levels:
            cms, tds, gvs, gss = [], [], [], []
            for size in SIZES:
                for rho in RHOS:
                    for delta in DELTAS:
                        if (rho, delta)[pick] != level:
                            continue
                        horizon = {i: recs[0]["horizon"] for (m, s, r, d, i), recs in runs.items()
                                   if (m, s, r, d) == (GILS, size, rho, delta)}
                        ms = inst(runs, GILS, size, rho, delta, "makespan")
                        td = inst(runs, GILS, size, rho, delta, "total_tardiness")
                        cms += [ms[i] / horizon[i] for i in ms]
                        tds += [td[i] / horizon[i] for i in td]
                        gvs += list(gains(runs, VAA, size, rho, delta).values())
                        gss += list(gains(runs, SA, size, rho, delta).values())
            print(f"{level:>6.2f}{mean(cms):>9.3f}{mean(tds):>9.3f}{mean(gvs):>+9.2f}{mean(gss):>+8.2f}")
        print()

    print("=== Paired tests between extreme levels (per instance, averaged over the other factor; 60 instances) ===")
    print("difference = value at the harder level minus value at the easier level")
    print(f"{'factor':<22}{'quantity':<12}{'mean diff':>10}{'p':>9}{'n':>4}")
    for label, pick, easy, hard in (("rho 0 -> 0.50", 0, 0.0, 0.50), ("delta inf -> 0.35", 1, float("inf"), 0.35)):
        for quantity in ("vs SA%", "vs VAA%", "Cmax/H", "tard./H"):
            diffs = []
            for size in SIZES:
                per = defaultdict(lambda: {easy: [], hard: []})
                for rho in RHOS:
                    for delta in DELTAS:
                        level = (rho, delta)[pick]
                        if level not in (easy, hard):
                            continue
                        if quantity == "vs SA%":
                            values = gains(runs, SA, size, rho, delta)
                        elif quantity == "vs VAA%":
                            values = gains(runs, VAA, size, rho, delta)
                        else:
                            field = "makespan" if quantity == "Cmax/H" else "total_tardiness"
                            raw = inst(runs, GILS, size, rho, delta, field)
                            horizon = {i: recs[0]["horizon"] for (m, s, r, d, i), recs in runs.items()
                                       if (m, s, r, d) == (GILS, size, rho, delta)}
                            values = {i: raw[i] / horizon[i] for i in raw}
                        for i, v in values.items():
                            per[i][level].append(v)
                diffs += [mean(v[hard]) - mean(v[easy]) for v in per.values()]
            p, n = wilcoxon_signed_rank(diffs)
            print(f"{label:<22}{quantity:<12}{mean(diffs):>+10.3f}{p:>9.4f}{n:>4}")

    print()
    print("Reading: gain% = 100 * (objective of the other method - objective of GILS) / objective of GILS;")
    print("positive means GILS-uniform is better. Cmax/H and tard./H divide by the horizon estimate H.")


if __name__ == "__main__":
    main()
