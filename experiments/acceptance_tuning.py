"""Tuning-pool check for the acceptance rule of the final engine.

Compares greedy acceptance (v2-GILS-ablate-none-1000) with SA acceptance plus
reheating (v2-GILS-ablate-addsa-1000) on the TUNING pool, so the design choice
does not rest on test-pool ablation results.

Usage:
    python experiments/acceptance_tuning.py
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
from experiments.runner import Job, run_jobs


OUTPUT = ROOT / "outputs" / "acceptance_tuning.jsonl"
SIZES = ("S", "M", "L")
TW_LEVELS = (None, "medium", "tight")
INDICES = (0, 1, 2, 3, 4)
REPS = (0, 1, 2, 3, 4)
GREEDY = "v2-GILS-ablate-none-1000"
SA = "v2-GILS-ablate-addsa-1000"


def tuning_jobs() -> list[Job]:
    jobs: list[Job] = []
    for size in SIZES:
        for tw in TW_LEVELS:
            for index in INDICES:
                common = dict(
                    pool="tuning",
                    size_class=size,
                    flow_pattern="uniform",
                    tw_tightness=tw,
                    index=index,
                )
                for method in (GREEDY, SA):
                    for rep in REPS:
                        jobs.append(Job(method=method, rep=rep, **common))
    return jobs


def summarize() -> None:
    values: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for line in OUTPUT.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        values[(r["size_class"], r["tw_tightness"], r["index"])][r["method"]].append(r["objective"])

    for scope, tw_filter in (("all", None), ("none", {None}), ("TW", {"medium", "tight"})):
        diffs = []
        for (size, tw, index), methods in sorted(values.items(), key=str):
            if tw_filter is not None and tw not in tw_filter:
                continue
            if GREEDY in methods and SA in methods:
                greedy = statistics.mean(methods[GREEDY])
                sa = statistics.mean(methods[SA])
                diffs.append(100.0 * (sa - greedy) / greedy)
        if not diffs:
            continue
        p, n = wilcoxon_signed_rank(diffs)
        print(f"SA vs greedy [{scope:<4}] n={n:>3}  mean={statistics.mean(diffs):+.3f}%p  p={p:.4f}")
    print("Positive mean = SA acceptance gives a worse objective than greedy.")


def main() -> None:
    executed = run_jobs(tuning_jobs(), OUTPUT, workers=6)
    print(f"acceptance tuning: executed {executed} new jobs -> {OUTPUT}")
    summarize()


if __name__ == "__main__":
    main()
