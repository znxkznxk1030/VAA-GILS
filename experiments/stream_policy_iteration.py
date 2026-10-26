"""Iterated policy improvement: Rollout over a learned base policy (TUNING set).

Generation k+1 = Rollout whose look-ahead base policy is the distilled network
of generation k (generation 1 = Rollout over FCFS-VAA, distilled into RL-API).
This script scores teachers on the same 12 tuning streams as every other
selection in this study, in parallel, so a generation can be judged before it
is distilled (experiments/stream_api_train.py --base <checkpoint>).

Usage:
    python experiments/stream_policy_iteration.py --teachers Rollout,Rollout@api --workers 7
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
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.sim import CrossDockStream, run_stream
from experiments.stream_rl_train import TUNING_BASE, TUNING_SET

OUT = ROOT / "outputs" / "stream_rl"


def load_net(name: str):
    from crossdock_solver.stream.rl import DispatchNet

    torch.set_num_threads(1)
    net = DispatchNet()
    net.load_state_dict(torch.load(OUT / f"{name}.pt"))
    return net.eval()


def make_teacher(spec: str, seed: int = 0, samples: int = 8):
    """"Rollout" (FCFS-VAA base) or "Rollout@<checkpoint>" (network base)."""

    from crossdock_solver.stream.rl import RLPolicy
    from crossdock_solver.stream.rollout import RolloutPolicy

    if spec == "Rollout":
        return RolloutPolicy(samples=samples, horizon_sla=1.0, seed=seed)
    name = spec.split("@", 1)[1]
    return RolloutPolicy(RLPolicy(load_net(name), name=name), samples=samples, horizon_sla=1.0, seed=seed, name=spec)


def _job(args):
    spec, k = args
    size, load, demand = TUNING_SET[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k,
                          measure_from=100, measure_to=500)
    start = time.perf_counter()
    metrics = run_stream(env, make_teacher(spec))
    return {"teacher": spec, "cell": k, "score": metrics.objective / env.facility.mean_work,
            "seconds": time.perf_counter() - start}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teachers", default="Rollout,Rollout@api")
    parser.add_argument("--workers", type=int, default=7)
    args = parser.parse_args()
    specs = args.teachers.split(",")
    jobs = [(s, k) for s in specs for k in range(len(TUNING_SET))]
    rows = []
    with multiprocessing.Pool(args.workers) as pool, (OUT / "policy_iteration.jsonl").open("a") as sink:
        for row in pool.imap_unordered(_job, jobs):
            rows.append(row)
            sink.write(json.dumps(row) + "\n")
            sink.flush()
    for s in specs:
        mine = [r for r in rows if r["teacher"] == s]
        print(f"{s:20} tuning J/work={np.mean([r['score'] for r in mine]):.4f} "
              f"({np.mean([r['seconds'] for r in mine]):.0f}s per stream)")


if __name__ == "__main__":
    main()
