"""Summary of the per-operator guided ablation (reviewer comment R1-16).

Contrasts are written "pool without gN -> pool with gN" (same convention as
b1_summary.py). A positive mean% means the pool WITH gN has the lower (better)
objective.
  generic -> add-gN : stand-alone effect of gN
  drop-gN -> full   : marginal effect of gN when the other guided operators are present

Statistics follow b1_summary.py: paired two-sided Wilcoxon signed-rank on
per-instance replication means, zero differences excluded from n. Holm-adjusted
p-values are reported over the eight contrasts within each scope.

Usage:
    python experiments/b1_individual_summary.py
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

FILES = (ROOT / "outputs" / "b1_guided_ablation.jsonl", ROOT / "outputs" / "b1_individual.jsonl")
TAGS = ("g1", "g2", "g3", "g4")
SCOPES = (("all", None), ("TW", {"medium", "tight"}), ("none", {None}))


def method(pool: str) -> str:
    return f"v2-GILS-{pool}-1000"


def load():
    objective: dict[tuple, float] = {}
    runtime: dict[str, list[float]] = defaultdict(list)
    for path in FILES:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if not r["method"].startswith("v2-GILS-"):
                continue
            objective[(r["method"], r["size_class"], r["tw_tightness"], r["index"], r["rep"])] = r["objective"]
            runtime[r["method"]].append(r["runtime_sec"])
    return objective, runtime


def instance_means(objective, pool, tw_filter):
    grouped = defaultdict(list)
    for (m, size, tw, index, rep), value in objective.items():
        if m == method(pool) and (tw_filter is None or tw in tw_filter):
            grouped[(size, tw, index)].append(value)
    return {key: statistics.mean(values) for key, values in grouped.items()}


def contrast(objective, with_pool, without_pool, tw_filter):
    """Relative difference (%) of instance means: positive = with_pool is better."""

    a = instance_means(objective, with_pool, tw_filter)
    b = instance_means(objective, without_pool, tw_filter)
    return [100.0 * (b[key] - a[key]) / a[key] for key in sorted(a, key=str) if key in b]


def holm(pvalues: list[float]) -> list[float]:
    order = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def main() -> None:
    objective, runtime = load()

    counts = defaultdict(int)
    for (m, *_rest) in objective:
        counts[m] += 1
    print("=== Runs per pool (expected 225) and mean runtime per run ===")
    for pool in ("generic", "critical", "full", *(f"add-{t}" for t in TAGS), *(f"drop-{t}" for t in TAGS)):
        print(f"{pool:<10}{counts[method(pool)]:>6}{statistics.mean(runtime[method(pool)]):>9.2f} s")

    contrasts = [(f"generic -> add-{t}", f"add-{t}", "generic") for t in TAGS]
    contrasts += [(f"drop-{t} -> full", "full", f"drop-{t}") for t in TAGS]

    for scope, tw_filter in SCOPES:
        rows = []
        for label, with_pool, without_pool in contrasts:
            diffs = contrast(objective, with_pool, without_pool, tw_filter)
            p, n = wilcoxon_signed_rank(diffs)
            wins = sum(d > 1e-12 for d in diffs)
            losses = sum(d < -1e-12 for d in diffs)
            rows.append((label, len(diffs), n, statistics.mean(diffs), p, wins, losses))
        adjusted = holm([row[4] for row in rows])
        print()
        print(f"=== Scope: {scope} ===")
        print(f"{'without gN -> with gN':<22}{'pairs':>6}{'n':>5}{'mean%':>9}{'p':>9}{'Holm p':>9}{'better':>8}{'worse':>7}")
        for row, adj in zip(rows, adjusted):
            label, pairs, n, mean, p, wins, losses = row
            print(f"{label:<22}{pairs:>6}{n:>5}{mean:>+9.3f}{p:>9.4f}{adj:>9.4f}{wins:>8}{losses:>7}")

    print()
    print("=== Consistency: cells without time windows (g3 -> g1, g4 -> g2 fallback) ===")
    for late, base in (("g3", "g1"), ("g4", "g2")):
        diffs = [
            abs(value - objective[(method(f"add-{base}"), size, tw, index, rep)])
            for (m, size, tw, index, rep), value in objective.items()
            if m == method(f"add-{late}") and tw is None
        ]
        print(f"add-{late} vs add-{base} on none cells: {len(diffs)} runs, max |difference| = {max(diffs):.6g}")

    print()
    print("Reading: mean% = 100 * (objective without gN - objective with gN) / objective with gN,")
    print("averaged over instances; positive means the guided operator lowers the objective.")
    print("'better'/'worse' count instances where the pool WITH gN has the lower/higher mean objective.")


if __name__ == "__main__":
    main()
