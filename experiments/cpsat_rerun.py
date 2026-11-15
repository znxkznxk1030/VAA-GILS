"""Re-run the 600 s CP-SAT reference on the M/L test cells, one job at a time.

The original CPSAT-600 records (2026-07-06) for the time-constrained M/L cells
report UNKNOWN after only 21-355 s of perf_counter time, which suggests the
machine was suspended while the solver's wall-clock limit kept running. This
script repeats those runs sequentially (no parallel jobs) and records both
perf_counter and wall-clock time so that a suspended run can be detected.

Run under `caffeinate -i` so the machine does not sleep:

    caffeinate -i python experiments/cpsat_rerun.py L        # sizes to run
    caffeinate -i python experiments/cpsat_rerun.py M L

Results are appended to outputs/cpsat_rerun.jsonl; finished jobs are skipped.
The original outputs/k1_results.jsonl is not touched.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.exact.cpsat import ExactCPSATConfig, solve_exact_cpsat
from experiments.methods import _auto_weight
from experiments.protocol import BenchmarkCell, cell_instance, cell_seed

OUTPUT = ROOT / "outputs" / "cpsat_rerun.jsonl"
TW_LEVELS = ("medium", "tight", None)
INDICES = (0, 1)
TIME_LIMIT = 600.0
SUSPEND_TOLERANCE = 15.0  # seconds of wall-clock time not accounted for by perf_counter


def main() -> None:
    sizes = [a for a in sys.argv[1:] if a in ("S", "M", "L")] or ["L"]
    # A run whose wall-clock time exceeds its perf_counter time was suspended
    # (e.g. the lid was closed): the solver's wall-clock limit kept running while
    # no computation happened. Such records are kept in the file but not counted
    # as done, so the job is repeated on the next invocation.
    done = set()
    if OUTPUT.exists():
        for line in OUTPUT.open():
            rec = json.loads(line)
            if rec["wall_sec"] - rec["runtime_sec"] <= SUSPEND_TOLERANCE:
                done.add(rec["key"])
    for size in sizes:
        for tw in TW_LEVELS:
            for index in INDICES:
                key = f"CPSAT-600-rerun|test|{size}|uniform|{tw or 'none'}|{index}"
                if key in done:
                    continue
                cell = BenchmarkCell(size_class=size, flow_pattern="uniform", tw_tightness=tw)
                instance = cell_instance("test", cell, index)
                print(f"### START {key} at {time.strftime('%H:%M:%S')}", flush=True)
                wall_start = time.time()
                result = solve_exact_cpsat(
                    instance,
                    ExactCPSATConfig(
                        time_limit_sec=TIME_LIMIT,
                        workers=8,
                        tardiness_weight=_auto_weight(instance),
                        msg=True,
                    ),
                )
                record = {
                    "key": key,
                    "method": "CPSAT-600-rerun",
                    "size_class": size,
                    "tw_tightness": tw,
                    "index": index,
                    "instance_seed": cell_seed("test", cell, index),
                    "status": result.status,
                    "proven_optimal": result.proven_optimal,
                    "objective": result.objective_value,
                    "lower_bound": result.lower_bound,
                    "runtime_sec": result.runtime_sec,
                    "wall_sec": time.time() - wall_start,
                    "finished_at": time.time(),
                }
                record["suspended"] = record["wall_sec"] - record["runtime_sec"] > SUSPEND_TOLERANCE
                with OUTPUT.open("a") as sink:
                    sink.write(json.dumps(record) + "\n")
                print(f"### DONE {json.dumps(record)}", flush=True)


if __name__ == "__main__":
    main()
