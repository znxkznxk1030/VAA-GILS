"""Fitness-landscape probe: is our problem big-valley (TSP-like) or rugged (QAP-like)?

Method. From many random feasible starts we run best-improvement descent to a
local optimum (the engine with max_iterations=0, restart/SA off, so only the
initial descent runs). For the collected local optima we measure:

  * dispersion in fitness  -- spread of local-optimum objectives (gap to the
    best local optimum found);
  * dispersion in space    -- normalized assignment distance between optima;
  * FDC (fitness-distance correlation) -- Pearson corr between an optimum's gap
    and its distance to the best optimum found. Strong positive FDC + low
    dispersion => big valley / single funnel (TSP-like); near-zero FDC + high
    dispersion => rugged multi-funnel (QAP-like).

Run on the TUNING pool (never test). Per size S/M/L to see the size trend.

    python experiments/landscape_analysis.py
writes outputs/landscape.jsonl, outputs/landscape_summary.txt, outputs/landscape_fdc.json
"""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.baselines.vaa_qrl import VaaQRLConfig, run_vaa_qrl
from crossdock_solver.initial.random_init import random_feasible_solution
from experiments.protocol import BenchmarkCell, cell_instance

SIZES = ("S", "M", "L")
TIGHTNESS = "medium"
INSTANCES = (0, 1, 2)
N_STARTS = 120
OUT = ROOT / "outputs" / "landscape.jsonl"
SUMMARY = ROOT / "outputs" / "landscape_summary.txt"
FDC_JSON = ROOT / "outputs" / "landscape_fdc.json"


def descent_local_optimum(instance, start):
    run = run_vaa_qrl(
        instance,
        VaaQRLConfig(
            max_iterations=0, use_descent=True, use_restart=False,
            use_sa_acceptance=False, tardiness_weight=1.0, seed=0,
        ),
        initial_solution=start,
    )
    obj = run.result.makespan + 1.0 * run.result.total_tardiness
    return obj, run.solution


def assignment_distance(a, b, trucks) -> float:
    """Normalized [0,1] assignment distance: per truck, destination + door mismatch."""
    diff = 0
    for t in trucks:
        if a.truck_destination(t) != b.truck_destination(t):
            diff += 1
        if a.truck_door(t) != b.truck_door(t):
            diff += 1
    return diff / (2 * len(trucks))


def pearson(xs, ys) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)


def main() -> None:
    records = []
    per_size = defaultdict(lambda: {"fdc": [], "gap": [], "meandist": [], "spread": []})
    for size in SIZES:
        for idx in INSTANCES:
            inst = cell_instance("tuning", BenchmarkCell(size, "uniform", TIGHTNESS), idx)
            trucks = list(inst.all_trucks)
            rng = random.Random(4242 + idx)
            optima = []  # (obj, solution)
            for k in range(N_STARTS):
                start = random_feasible_solution(inst, rng)
                obj, sol = descent_local_optimum(inst, start)
                optima.append((obj, sol))
            best_obj = min(o for o, _ in optima)
            best_sol = min(optima, key=lambda t: t[0])[1]
            gaps, dists = [], []
            for o, s in optima:
                g = 100.0 * (o - best_obj) / best_obj
                d = assignment_distance(s, best_sol, trucks)
                gaps.append(g)
                dists.append(d)
                records.append({"size": size, "index": idx, "obj": o,
                                "gap_to_best": g, "dist_to_best": d})
            fdc = pearson(gaps, dists)
            # mean pairwise distance among a sample of optima (space dispersion)
            sample = [s for _, s in optima[:40]]
            pd = [assignment_distance(sample[i], sample[j], trucks)
                  for i in range(len(sample)) for j in range(i + 1, len(sample))]
            meandist = sum(pd) / len(pd) if pd else float("nan")
            spread = (max(gaps))  # worst local optimum gap%
            per_size[size]["fdc"].append(fdc)
            per_size[size]["gap"].append(sum(gaps) / len(gaps))
            per_size[size]["meandist"].append(meandist)
            per_size[size]["spread"].append(spread)
            print(f"  {size} idx{idx}: FDC={fdc:+.3f}  mean gap={sum(gaps)/len(gaps):.2f}%  "
                  f"max gap={spread:.2f}%  mean pairwise dist={meandist:.3f}", flush=True)

    OUT.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    fdc_summary = {}
    lines = ["=== Fitness-landscape probe (tuning pool, medium TW) ==="]
    lines.append(f"{N_STARTS} random-start descents x {len(INSTANCES)} instances per size")
    lines.append(f"{'size':>5}{'FDC':>9}{'mean gap%':>11}{'max gap%':>10}{'pairwise dist':>15}")
    for size in SIZES:
        d = per_size[size]
        fdc = sum(d["fdc"]) / len(d["fdc"])
        gap = sum(d["gap"]) / len(d["gap"])
        mx = sum(d["spread"]) / len(d["spread"])
        md = sum(d["meandist"]) / len(d["meandist"])
        fdc_summary[size] = {"fdc": fdc, "mean_gap": gap, "max_gap": mx, "mean_pairwise_dist": md}
        lines.append(f"{size:>5}{fdc:>+9.3f}{gap:>11.2f}{mx:>10.2f}{md:>15.3f}")
    lines.append("")
    lines.append("Interpretation: FDC near +1 with small gaps and modest distance-to-best")
    lines.append("=> big valley / single funnel (TSP-like). FDC near 0 with large")
    lines.append("dispersion => rugged multi-funnel (QAP-like).")
    text = "\n".join(lines)
    SUMMARY.write_text(text + "\n")
    FDC_JSON.write_text(json.dumps(fdc_summary, indent=1))
    print("\n" + text)
    print(f"\nwrote {OUT}\nwrote {SUMMARY}\nwrote {FDC_JSON}")


if __name__ == "__main__":
    main()
