"""B1 (individual): per-operator guided ablation for reviewer comment R1-16.

Same protocol as experiments/b1_run.py (uniform selection, final engine, 1,000
iterations, test pool, 9 cells x 5 instances x 5 replications), but the operator
pools isolate one guided operator at a time:

  add-gN  = generic + gN        (stand-alone effect, compared with generic)
  drop-gN = full without gN     (marginal effect, compared with full)

The generic / critical / full arms are NOT re-run here; they are read from
outputs/b1_guided_ablation.jsonl by the summary script. Pass --check to re-run a
few `full` jobs into a scratch file and compare them with the stored values.

Usage:
    python experiments/b1_individual_run.py
    python experiments/b1_individual_run.py --check
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.methods import INDIVIDUAL_POOLS
from experiments.runner import Job, run_jobs


OUTPUT = ROOT / "outputs" / "b1_individual.jsonl"
BASELINE = ROOT / "outputs" / "b1_guided_ablation.jsonl"
CHECK_OUTPUT = ROOT / "outputs" / "b1_individual_check.jsonl"

SIZES = ("S", "M", "L")
TW_LEVELS = (None, "medium", "tight")
INDICES = (0, 1, 2, 3, 4)
REPS = (0, 1, 2, 3, 4)


def jobs_for(pools, sizes=SIZES, indices=INDICES, reps=REPS) -> list[Job]:
    jobs: list[Job] = []
    for size in sizes:
        for tw in TW_LEVELS:
            for index in indices:
                for pool in pools:
                    for rep in reps:
                        jobs.append(
                            Job(
                                method=f"v2-GILS-{pool}-1000",
                                rep=rep,
                                pool="test",
                                size_class=size,
                                flow_pattern="uniform",
                                tw_tightness=tw,
                                index=index,
                            )
                        )
    return jobs


def check_reproduction() -> None:
    """Re-run a few stored `full` jobs and compare objectives exactly."""

    if CHECK_OUTPUT.exists():
        CHECK_OUTPUT.unlink()
    run_jobs(jobs_for(("full",), sizes=("S", "M"), indices=(0,), reps=(0, 1)), CHECK_OUTPUT, workers=4)
    stored = {}
    for line in BASELINE.read_text().splitlines():
        r = json.loads(line)
        if r["method"] == "v2-GILS-full-1000":
            stored[(r["size_class"], r["tw_tightness"], r["index"], r["rep"])] = r["objective"]
    worst = 0.0
    count = 0
    for line in CHECK_OUTPUT.read_text().splitlines():
        r = json.loads(line)
        key = (r["size_class"], r["tw_tightness"], r["index"], r["rep"])
        worst = max(worst, abs(r["objective"] - stored[key]))
        count += 1
    print(f"check: {count} re-run full jobs, max |objective difference| = {worst:.6g}")


def main() -> None:
    if "--check" in sys.argv:
        check_reproduction()
        return
    executed = run_jobs(jobs_for(INDIVIDUAL_POOLS), OUTPUT, workers=6)
    print(f"b1_individual: executed {executed} new jobs -> {OUTPUT}")


if __name__ == "__main__":
    main()
