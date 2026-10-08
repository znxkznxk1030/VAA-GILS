"""Continuous cross-dock: limitations of VAA-GILS and the RL dispatcher (TEST pool).

Grid: sizes S/M/L x load 0.5/0.6/0.7 x demand uniform/skewed, 5 test seeds per
cell, measurement window = trucks 200..1199 of each stream. L is never seen in
training (generalization). Methods:

    FCFS-VAA, FCFS-Backlog                 dispatching rules
    Cyclic-VAA, Cyclic-GILS               the static method in cycles of |D| trucks
    Cyclic-GILS-strict                    same plan, executed on the planned doors
    RL-BC                                 the network after imitation only
    RL-PPO                                the selected PPO checkpoint

Usage:
    python experiments/stream_eval.py --policy outputs/stream_rl/ppo_bc.pt   # run + summarize
    python experiments/stream_eval.py summary
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

import numpy as np
from scipy.stats import wilcoxon

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.sim import CrossDockStream, run_stream


OUTPUT = ROOT / "outputs" / "stream_eval.jsonl"
TEST_BASE = 300_000
SIZES = ("S", "M", "L")
LOADS = (0.5, 0.6, 0.7)
DEMANDS = ("uniform", "skewed")
SEEDS = range(5)
METHODS = ("FCFS-VAA", "FCFS-Backlog", "Cyclic-VAA", "Cyclic-GILS", "Cyclic-GILS-strict", "RL-BC", "RL-PPO")
CELLS = [(s, l, d) for s in SIZES for l in LOADS for d in DEMANDS]


def _seed(cell: tuple, rep: int) -> int:
    return TEST_BASE + 1_000 * CELLS.index(cell) + rep


_NETS: dict[str, object] = {}


def _net(kind: str, policy_path: str):
    import torch

    from crossdock_solver.stream.rl import DispatchNet, TrainConfig, behaviour_clone

    if kind not in _NETS:
        torch.set_num_threads(1)
        torch.manual_seed(0)
        net = DispatchNet()
        if kind == "RL-BC":
            behaviour_clone(net, TrainConfig(bc_episodes=16))
        else:
            net.load_state_dict(torch.load(policy_path))
        net.eval()
        _NETS[kind] = net
    return _NETS[kind]


def _policy(method: str, policy_path: str):
    from crossdock_solver.stream.policies import CyclicPlanPolicy, FCFSRulePolicy
    from crossdock_solver.stream.rl import RLPolicy

    if method == "FCFS-VAA":
        return FCFSRulePolicy()
    if method == "FCFS-Backlog":
        return FCFSRulePolicy(backlog=True)
    if method == "Cyclic-VAA":
        return CyclicPlanPolicy(iterations=0)
    if method == "Cyclic-GILS":
        return CyclicPlanPolicy(iterations=1000)
    if method == "Cyclic-GILS-strict":
        return CyclicPlanPolicy(iterations=1000, execution="strict")
    if method in ("RL-BC", "RL-PPO"):
        return RLPolicy(_net(method, policy_path), name=method)
    raise ValueError(method)


class _Counting:
    """Wraps a policy to time decisions and count holds."""

    def __init__(self, inner) -> None:
        self.inner = inner
        self.decisions = 0
        self.holds = 0
        self.seconds = 0.0
        self.max_seconds = 0.0

    def reset(self, env) -> None:
        if hasattr(self.inner, "reset"):
            self.inner.reset(env)

    def act(self, env):
        start = time.perf_counter()
        action = self.inner.act(env)
        elapsed = time.perf_counter() - start
        self.decisions += 1
        self.holds += action is None
        self.seconds += elapsed
        self.max_seconds = max(self.max_seconds, elapsed)
        return action


def _execute(job: tuple) -> dict:
    method, size, load, demand, rep, policy_path = job
    cell = (size, load, demand)
    env = CrossDockStream(
        stream_config(size, load=load, demand=demand),
        seed=_seed(cell, rep),
        measure_from=200,
        measure_to=1200,
    )
    policy = _Counting(_policy(method, policy_path))
    metrics = run_stream(env, policy)
    record = {
        "key": f"{method}|{size}|{load}|{demand}|{rep}",
        "method": method,
        "size": size,
        "load": load,
        "demand": demand,
        "rep": rep,
        "mean_work": env.facility.mean_work,
        **metrics.as_dict(),
        "decisions": policy.decisions,
        "hold_rate": policy.holds / max(policy.decisions, 1),
        "decide_ms_mean": 1000 * policy.seconds / max(policy.decisions, 1),
        "decide_ms_max": 1000 * policy.max_seconds,
    }
    inner = policy.inner
    if hasattr(inner, "cycle_wait"):
        record["cycle_wait"] = float(np.mean(inner.cycle_wait)) if inner.cycle_wait else 0.0
        record["plan_ms_mean"] = 1000 * float(np.mean(inner.plan_seconds)) if inner.plan_seconds else 0.0
        record["plan_ms_max"] = 1000 * float(np.max(inner.plan_seconds)) if inner.plan_seconds else 0.0
    return record


def run(policy_path: str, workers: int = 6, methods: tuple[str, ...] = METHODS) -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    jobs = [
        (m, s, l, d, r, policy_path)
        for (s, l, d) in CELLS
        for r in SEEDS
        for m in methods
        if f"{m}|{s}|{l}|{d}|{r}" not in done
    ]
    if not jobs:
        return 0
    # slow strict-execution jobs first for better load balance
    jobs.sort(key=lambda j: (j[0] != "Cyclic-GILS-strict", j[0] != "Cyclic-GILS"))
    with OUTPUT.open("a", encoding="utf-8") as sink, multiprocessing.Pool(workers) as pool:
        for record in pool.imap_unordered(_execute, jobs):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    return len(jobs)


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    by = {(r["method"], r["size"], r["load"], r["demand"], r["rep"]): r for r in records}
    norm = lambda r: r["objective"] / r["mean_work"]  # noqa: E731
    out: list[str] = []

    out.append("Normalized objective J / mean truck work (mean over 5 test streams)")
    header = f"{'size':4} {'load':4} {'demand':8}" + "".join(f"{m:>19}" for m in METHODS)
    out.append(header)
    for size, load, demand in CELLS:
        row = []
        for m in METHODS:
            vals = [norm(by[(m, size, load, demand, r)]) for r in SEEDS if (m, size, load, demand, r) in by]
            row.append(f"{statistics.mean(vals):19.3f}" if vals else f"{'-':>19}")
        out.append(f"{size:4} {load:<4} {demand:8}" + "".join(row))

    out.append("")
    out.append("Relative to FCFS-VAA (%; mean of per-stream ratios, negative = better)")
    for scope in (*SIZES, "all"):
        cells = [c for c in CELLS if scope in ("all", c[0])]
        parts = []
        for m in METHODS:
            ratios = [
                100 * (norm(by[(m, *c, r)]) / norm(by[("FCFS-VAA", *c, r)]) - 1)
                for c in cells
                for r in SEEDS
                if (m, *c, r) in by and ("FCFS-VAA", *c, r) in by
            ]
            parts.append(f"{m}={statistics.mean(ratios):+.1f}" if ratios else f"{m}=-")
        out.append(f"  {scope:3}: " + "  ".join(parts))

    out.append("")
    out.append("Paired Wilcoxon (two-sided) of RL-PPO vs each method, per-stream J")
    for m in METHODS:
        if m == "RL-PPO":
            continue
        for scope in (*SIZES, "all"):
            pairs = [
                (norm(by[("RL-PPO", *c, r)]), norm(by[(m, *c, r)]))
                for c in CELLS
                if scope in ("all", c[0])
                for r in SEEDS
                if ("RL-PPO", *c, r) in by and (m, *c, r) in by
            ]
            if len(pairs) < 6:
                continue
            diffs = [a - b for a, b in pairs]
            wins = sum(d < 0 for d in diffs)
            p = wilcoxon(diffs).pvalue if any(diffs) else 1.0
            out.append(f"  vs {m:19} {scope:3} n={len(pairs):3} RL better in {wins:3}  p={p:.2g}")

    out.append("")
    out.append("Diagnostics (mean over all streams of a size)")
    keys = ("mean_lead", "mean_tardiness", "mean_yard_wait", "utilization", "empty_outbound_rate",
            "undelivered_units", "hold_rate", "decide_ms_mean", "decide_ms_max", "cycle_wait", "plan_ms_mean", "plan_ms_max")
    for size in SIZES:
        out.append(f"  size {size}")
        for m in METHODS:
            rows = [r for r in records if r["method"] == m and r["size"] == size]
            if not rows:
                continue
            vals = []
            for k in keys:
                xs = [r[k] for r in rows if k in r]
                if xs:
                    vals.append(f"{k}={statistics.mean(xs):.3g}")
            out.append(f"    {m:19} " + " ".join(vals))
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="run")
    parser.add_argument("--policy", default=str(ROOT / "outputs" / "stream_rl" / "ppo_bc.pt"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--methods", default=",".join(METHODS))
    args = parser.parse_args()
    if args.mode != "summary":
        executed = run(args.policy, args.workers, tuple(args.methods.split(",")))
        print(f"executed {executed} new jobs -> {OUTPUT}")
    print(summarize())


if __name__ == "__main__":
    main()
