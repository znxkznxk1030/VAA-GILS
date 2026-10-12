"""Compound-truck ratio sensitivity: does the VAA-GILS advantage hold when |I|/(|I|+|F|) changes?

The main benchmark fixes the compound fraction at 2/3. Here the M-size total of
18 trucks (= 18 destinations) is split differently. Feasibility of the model:
every compound truck occupies its own door in the first stage, so |I| <= |M|
(doors). The paper's M has 12 doors, so 15 compound trucks are infeasible there.
Two grids are therefore run:

    doors15 : |I| in {6, 12, 15}  (|F| = 12, 6, 3)   the requested ratios at a common door count
    doors12 : |I| in {6, 9, 12}   (|F| = 12, 9, 6)   the paper's M door count

x TW in {none, medium, tight} x 20 instances (uniform flow, synthetic profile,
same generator as the benchmark). Methods and settings are the frozen ones of
the main comparison: VAA, SA-RL5 1,000 iterations (Paper-SA-RL5 on TW none,
Extended-SA-RL5 on medium/tight), VAA-GILS 1,000 iterations (v2-GILS-uniform-1000),
5 replications for the stochastic methods.

Seeds: test pool, offset 60000 (disjoint from benchmark cells, which use < 48000).

Usage:
    python experiments/compound_ratio.py --workers 4   # run missing jobs + summarize
    python experiments/compound_ratio.py summary
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import multiprocessing
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.data.generator import generate_random_instance
from experiments.k1_stats import wilcoxon_signed_rank
from experiments.methods import METHOD_REGISTRY


OUTPUT = ROOT / "outputs" / "compound_ratio.jsonl"
SEED_BASE = 300_000 + 60_000
TOTAL_TRUCKS = 18
GRIDS = {"doors15": (15, (6, 12, 15)), "doors12": (12, (6, 9, 12))}
TW_LEVELS = (None, "medium", "tight")
INDICES = tuple(range(20))
REPS = tuple(range(5))
GROUPS = ("VAA", "SA-RL5", "VAA-GILS")


def cells() -> list[tuple[str, int, int, str | None]]:
    return [
        (grid, doors, compounds, tw)
        for grid, (doors, compound_counts) in GRIDS.items()
        for compounds in compound_counts
        for tw in TW_LEVELS
    ]


def instance_seed(doors: int, compounds: int, tw: str | None, index: int) -> int:
    grid = next(g for g, (d, _) in GRIDS.items() if d == doors)
    return SEED_BASE + cells().index((grid, doors, compounds, tw)) * 1_000 + index


def method_name(group: str, tw: str | None) -> str:
    if group == "VAA":
        return "VAA"
    if group == "VAA-GILS":
        return "v2-GILS-uniform-1000"
    return "Paper-SA-RL5-1000" if tw is None else "Extended-SA-RL5-1000"


def jobs() -> list[tuple]:
    out = []
    for grid, doors, compounds, tw in cells():
        for index in INDICES:
            for group in GROUPS:
                for rep in (REPS if group != "VAA" else (0,)):
                    out.append((group, grid, doors, compounds, tw, index, rep))
    return out


def key(job: tuple) -> str:
    group, grid, doors, compounds, tw, index, rep = job
    return f"{group}|{grid}|{doors}|{compounds}|{tw or 'none'}|{index}|{rep}"


def execute(job: tuple) -> dict:
    group, grid, doors, compounds, tw, index, rep = job
    seed = instance_seed(doors, compounds, tw, index)
    instance = generate_random_instance(
        num_compounds=compounds,
        num_outbounds=TOTAL_TRUCKS - compounds,
        num_doors=doors,
        seed=seed,
        flow_pattern="uniform",
        tw_tightness=tw,
    )
    method = method_name(group, tw)
    result = METHOD_REGISTRY[method](instance, seed * 100 + rep, None)
    if "objective" not in result:  # Paper-SA-RL5 on TW none: objective is the makespan
        result["objective"] = result["makespan"]
    return {
        "key": key(job),
        "group": group,
        "method": method,
        "grid": grid,
        "doors": doors,
        "compounds": compounds,
        "outbounds": TOTAL_TRUCKS - compounds,
        "tw": tw or "none",
        "index": index,
        "rep": rep,
        "instance_seed": seed,
        "finished_at": time.time(),
        **result,
    }


def run(workers: int) -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    pending = [j for j in jobs() if key(j) not in done]
    if not pending:
        return 0
    with OUTPUT.open("a", encoding="utf-8") as sink, multiprocessing.Pool(workers) as pool:
        for record in pool.imap_unordered(execute, pending, chunksize=4):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    return len(pending)


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    # per (cell, index): mean objective of each group over replications, best observed over all runs
    runs: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    secs: dict[tuple, list[float]] = defaultdict(list)
    for r in records:
        cell = (r["grid"], r["compounds"], r["tw"])
        runs[(*cell, r["index"])][r["group"]].append(r["objective"])
        secs[(*cell, r["group"])].append(r["runtime_sec"])

    out = ["Compound-truck ratio sensitivity (M total 18 trucks, 20 instances per cell, 5 reps for SA-RL5/GILS)",
           "gap = mean % above the best objective observed on the instance over all runs (lower is better);",
           "impr = per-instance % improvement of VAA-GILS over the method (positive = GILS better), Wilcoxon on instance means", ""]
    header = (f"{'grid':8}{'|I|/|F|':>8}{'ratio':>7}{'TW':>8}{'n':>4}"
              + "".join(f"{g + ' gap':>13}" for g in GROUPS)
              + f"{'impr vs VAA':>13}{'p':>9}{'impr vs SA':>12}{'p':>9}{'GILS<SA':>9}{'GILS s':>8}")
    out.append(header)

    def block(rows_keys, label):
        gaps = {g: [] for g in GROUPS}
        impr = {"VAA": [], "SA-RL5": []}
        diffs = {"VAA": [], "SA-RL5": []}
        for k in rows_keys:
            by = runs[k]
            if not all(by.get(g) for g in GROUPS):
                continue
            best = min(min(v) for v in by.values())
            means = {g: statistics.mean(by[g]) for g in GROUPS}
            for g in GROUPS:
                gaps[g].append(100 * (means[g] / best - 1))
            for g in ("VAA", "SA-RL5"):
                impr[g].append(100 * (1 - means["VAA-GILS"] / means[g]))
                diffs[g].append(means["VAA-GILS"] - means[g])
        n = len(gaps["VAA"])
        if not n:
            return None
        p_vaa, _ = wilcoxon_signed_rank(diffs["VAA"])
        p_sa, _ = wilcoxon_signed_rank(diffs["SA-RL5"])
        wins = sum(d < 0 for d in diffs["SA-RL5"])
        return (label, n, gaps, impr, p_vaa, p_sa, wins)

    def fmt(prefix, result, gils_sec):
        label, n, gaps, impr, p_vaa, p_sa, wins = result
        return (prefix + f"{n:4d}" + "".join(f"{statistics.mean(gaps[g]):13.2f}" for g in GROUPS)
                + f"{statistics.mean(impr['VAA']):+13.2f}{p_vaa:9.1e}{statistics.mean(impr['SA-RL5']):+12.2f}"
                f"{p_sa:9.1e}{wins:6d}/{n:<2d}{gils_sec:8.2f}")

    for grid, (doors, compound_counts) in GRIDS.items():
        for compounds in compound_counts:
            ratio = compounds / TOTAL_TRUCKS
            for tw in (*[t or "none" for t in TW_LEVELS], "all"):
                tws = [t or "none" for t in TW_LEVELS] if tw == "all" else [tw]
                ks = [(grid, compounds, t, i) for t in tws for i in INDICES]
                res = block(ks, tw)
                if res is None:
                    continue
                gsec = [s for t in tws for s in secs[(grid, compounds, t, "VAA-GILS")]]
                prefix = f"{grid:8}{f'{compounds}/{TOTAL_TRUCKS - compounds}':>8}{ratio:7.2f}{tw:>8}"
                out.append(fmt(prefix, res, statistics.mean(gsec) if gsec else float('nan')))
            out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="run")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.mode != "summary":
        print(f"executed {run(args.workers)} new jobs -> {OUTPUT}", flush=True)
    print(summarize())


if __name__ == "__main__":
    main()
