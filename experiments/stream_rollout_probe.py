"""Headroom probe on the TUNING set: rollout policy improvement over FCFS-VAA.

Usage:
    python experiments/stream_rollout_probe.py --samples 8 --horizon 1.0
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.rollout import RolloutPolicy
from crossdock_solver.stream.sim import CrossDockStream, run_stream
from experiments.stream_rl_train import TUNING_BASE, TUNING_SET


def _one(job):
    k, samples, horizon = job
    size, load, demand = TUNING_SET[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k, measure_from=100, measure_to=500)
    start = time.perf_counter()
    metrics = run_stream(env, RolloutPolicy(samples=samples, horizon_sla=horizon))
    return k, metrics.objective / env.facility.mean_work, time.perf_counter() - start


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--horizon", type=float, default=1.0)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    jobs = [(k, args.samples, args.horizon) for k in range(len(TUNING_SET))]
    with multiprocessing.Pool(args.workers) as pool:
        results = sorted(pool.map(_one, jobs))
    scores = [s for _, s, _ in results]
    out = {
        "samples": args.samples,
        "horizon_sla": args.horizon,
        "tuning_score": float(np.mean(scores)),
        "per_stream": [round(s, 4) for s in scores],
        "sec_per_stream": float(np.mean([t for _, _, t in results])),
    }
    print(json.dumps(out))
    path = ROOT / "outputs" / "stream_rl" / "rollout_probe.jsonl"
    with path.open("a") as sink:
        sink.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
