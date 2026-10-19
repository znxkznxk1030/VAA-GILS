"""Tune the rolling-horizon baseline (RollingHorizonPolicy) on the TUNING set.

The only free parameter is the terminal delay of the sweeper (how long the
plan assumes stranded freight waits for a future carrier, in units of |D|
interarrival times + mean truck work). Each value is scored by the mean J/work
over the same 12 tuning streams as the RL checkpoints and the tuned rules
(seeds 200000+k, trucks 100..499); the best value is written to
outputs/stream_rl/rolling.json. The TEST pool is not touched.

Usage:
    python experiments/stream_rolling_tune.py --workers 7
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.sim import CrossDockStream, run_stream

OUT = ROOT / "outputs" / "stream_rl"
TUNING_BASE = 200_000
CELLS = [(s, l, d) for s in ("S", "M") for l in (0.5, 0.6, 0.7) for d in ("uniform", "skewed")]
TERMINALS = (0.5, 1.0, 1.5, 2.0, 3.0)
TIME_LIMIT = 1.0


def _job(args: tuple) -> dict:
    from crossdock_solver.stream.rolling import RollingHorizonPolicy

    terminal, k = args
    size, load, demand = CELLS[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k,
                          measure_from=100, measure_to=500)
    policy = RollingHorizonPolicy(time_limit=TIME_LIMIT, terminal=terminal)
    metrics = run_stream(env, policy)
    return {"terminal": terminal, "cell": k, "score": metrics.objective / env.facility.mean_work,
            "solves": policy.solves, "fallbacks": policy.fallbacks, "optimal": policy.optimal}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=7)
    args = parser.parse_args()
    jobs = [(t, k) for t in TERMINALS for k in range(len(CELLS))]
    log = OUT / "rolling_tune.jsonl"
    with multiprocessing.Pool(args.workers) as pool, log.open("w", encoding="utf-8") as sink:
        rows = []
        for row in pool.imap_unordered(_job, jobs):
            rows.append(row)
            sink.write(json.dumps(row) + "\n")
            sink.flush()
    scores = {t: float(np.mean([r["score"] for r in rows if r["terminal"] == t])) for t in TERMINALS}
    best = min(scores, key=scores.get)
    summary = {"terminal": best, "time_limit": TIME_LIMIT, "tuning_scores": scores,
               "fallback_rate": {t: sum(r["fallbacks"] for r in rows if r["terminal"] == t)
                                 / max(1, sum(r["solves"] for r in rows if r["terminal"] == t)) for t in TERMINALS}}
    (OUT / "rolling.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
