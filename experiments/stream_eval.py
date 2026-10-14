"""Continuous cross-dock: limitations of VAA-GILS and the RL dispatcher (TEST pool).

Grid: sizes S/M/L x load 0.5/0.6/0.7 x demand uniform/skewed, 5 test seeds per
cell, measurement window = trucks 200..1199 of each stream. L is never seen in
training (generalization). Methods:

    FCFS-VAA, FCFS-Backlog                 dispatching rules
    SPT-VAA, Random                       shortest-processing-time sequencing, random dispatching
    Tuned-Rule                            linear priority rule tuned by CEM on train/tuning pools (stream_rule_tune.py)
    Tuned-Linear                          linear score over the RL network's 24 candidate features (same information), tuned likewise
    Cyclic-VAA, Cyclic-SA-RL5, Cyclic-GILS the static methods of the JKIIE study in cycles of |D| trucks
                                          (SA-RL5 = original paper's Q-learning SA, objective with tardiness)
    Cyclic-CPSAT                          each cycle solved by CP-SAT (per-cycle optimum reference)
    Cyclic-GILS-strict                    same plan, executed on the planned doors
    RL-BC                                 the network after imitation only
    RL-PPO                                the PPO checkpoint selected on tuning
    Rollout                               simulation-based policy improvement over FCFS-VAA
    RL-API                                the network distilled from Rollout (DAgger)

Usage:
    python experiments/stream_eval.py              # run missing jobs + summarize
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

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.sim import CrossDockStream, run_stream
from experiments.k1_stats import wilcoxon_signed_rank  # scipy is broken in this env (NumPy ABI)


OUTPUT = ROOT / "outputs" / "stream_eval.jsonl"
TEST_BASE = 300_000
SIZES = ("S", "M", "L")
LOADS = (0.5, 0.6, 0.7)
DEMANDS = ("uniform", "skewed")
SEEDS = range(5)
METHODS = (
    "FCFS-VAA",
    "FCFS-Backlog",
    "SPT-VAA",
    "Random",
    "Tuned-Rule",
    "Tuned-Linear",
    "Cyclic-VAA",
    "Cyclic-SA-RL5",
    "Cyclic-GILS",
    "Cyclic-CPSAT",
    "Cyclic-GILS-strict",
    "RL-BC",
    "RL-PPO",
    "Rollout",
    "RL-API",
)
CHECKPOINTS = {
    "RL-PPO": ROOT / "outputs" / "stream_rl" / "ppo2_tau1.pt",
    "RL-API": ROOT / "outputs" / "stream_rl" / "api.pt",
}
BOUNDS = ROOT / "outputs" / "stream_bounds.jsonl"
TUNED_RULE = ROOT / "outputs" / "stream_rl" / "tuned_rule.json"
TUNED_LINEAR = ROOT / "outputs" / "stream_rl" / "tuned_linear.json"
# references for the relative tables ("how much better than X")
REFERENCES = ("FCFS-VAA", "Cyclic-VAA", "Cyclic-SA-RL5", "Cyclic-GILS", "Cyclic-CPSAT")
CELLS = [(s, l, d) for s in SIZES for l in LOADS for d in DEMANDS]


def _seed(cell: tuple, rep: int) -> int:
    return TEST_BASE + 1_000 * CELLS.index(cell) + rep


_NETS: dict[str, object] = {}


def _net(kind: str):
    import torch

    from crossdock_solver.stream.rl import DispatchNet, TrainConfig, behaviour_clone

    if kind not in _NETS:
        torch.set_num_threads(1)
        torch.manual_seed(0)
        net = DispatchNet()
        if kind == "RL-BC":
            behaviour_clone(net, TrainConfig(bc_episodes=16))
        else:
            net.load_state_dict(torch.load(CHECKPOINTS[kind]))
        net.eval()
        _NETS[kind] = net
    return _NETS[kind]


def _policy(method: str):
    from crossdock_solver.stream.policies import CyclicPlanPolicy, FCFSRulePolicy, RandomPolicy, SPTRulePolicy
    from crossdock_solver.stream.rl import RLPolicy

    if method == "FCFS-VAA":
        return FCFSRulePolicy()
    if method == "FCFS-Backlog":
        return FCFSRulePolicy(backlog=True)
    if method == "SPT-VAA":
        return SPTRulePolicy()
    if method == "Random":
        return RandomPolicy()
    if method == "Tuned-Rule":
        from crossdock_solver.stream.policies import PriorityRulePolicy

        tuned = json.loads(TUNED_RULE.read_text())
        return PriorityRulePolicy(tuned["weights"], tuned["threshold"])
    if method == "Tuned-Linear":
        from crossdock_solver.stream.rl import LinearScorePolicy

        return LinearScorePolicy(json.loads(TUNED_LINEAR.read_text())["weights"], name="Tuned-Linear")
    if method == "Cyclic-VAA":
        return CyclicPlanPolicy(iterations=0)
    if method == "Cyclic-SA-RL5":
        return CyclicPlanPolicy(iterations=1000, solver="sa-rl5")
    if method == "Cyclic-GILS":
        return CyclicPlanPolicy(iterations=1000)
    if method == "Cyclic-CPSAT":
        return CyclicPlanPolicy(solver="cpsat", cpsat_time_limit=10.0)
    if method == "Cyclic-GILS-strict":
        return CyclicPlanPolicy(iterations=1000, execution="strict")
    if method in ("RL-BC", "RL-PPO", "RL-API"):
        return RLPolicy(_net(method), name=method)
    if method == "Rollout":
        from crossdock_solver.stream.rollout import RolloutPolicy

        return RolloutPolicy(samples=8, horizon_sla=1.0)
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
    method, size, load, demand, rep = job
    cell = (size, load, demand)
    env = CrossDockStream(
        stream_config(size, load=load, demand=demand),
        seed=_seed(cell, rep),
        measure_from=200,
        measure_to=1200,
    )
    policy = _Counting(_policy(method))
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
        if inner.solver == "cpsat":
            record["cycles"] = len(inner.plan_seconds)
            record["cpsat_optimal_cycles"] = inner.cpsat_optimal
    return record


def run(workers: int = 6, methods: tuple[str, ...] = METHODS, sizes: tuple[str, ...] = SIZES) -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    jobs = [
        (m, s, l, d, r)
        for (s, l, d) in CELLS
        if s in sizes
        for r in SEEDS
        for m in methods
        if f"{m}|{s}|{l}|{d}|{r}" not in done
    ]
    if not jobs:
        return 0
    # slow jobs first for better load balance
    slow = {"Cyclic-CPSAT": 0, "Rollout": 1, "Cyclic-GILS-strict": 2, "Cyclic-GILS": 3, "Cyclic-SA-RL5": 3}
    jobs.sort(key=lambda j: (slow.get(j[0], 9), "LMS".index(j[1])))
    with OUTPUT.open("a", encoding="utf-8") as sink, multiprocessing.Pool(workers) as pool:
        for record in pool.imap_unordered(_execute, jobs):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    return len(jobs)


def _bound(job: tuple) -> dict:
    from crossdock_solver.stream.bounds import stream_lower_bound
    from crossdock_solver.stream.policies import FCFSRulePolicy

    size, load, demand, rep = job
    cell = (size, load, demand)
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=_seed(cell, rep),
                          measure_from=200, measure_to=1200)
    run_stream(env, FCFSRulePolicy())  # any policy: the measured trucks do not depend on it
    return {"key": f"{size}|{load}|{demand}|{rep}", "size": size, "load": load, "demand": demand, "rep": rep,
            "mean_work": env.facility.mean_work, "lower_bound": stream_lower_bound(env)}


def bounds(workers: int, sizes: tuple[str, ...]) -> int:
    done = set()
    if BOUNDS.exists():
        done = {json.loads(line)["key"] for line in BOUNDS.read_text().splitlines() if line}
    jobs = [(s, l, d, r) for (s, l, d) in CELLS if s in sizes for r in SEEDS if f"{s}|{l}|{d}|{r}" not in done]
    with BOUNDS.open("a", encoding="utf-8") as sink, multiprocessing.Pool(workers) as pool:
        for record in pool.imap_unordered(_bound, jobs):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    return len(jobs)


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    by = {(r["method"], r["size"], r["load"], r["demand"], r["rep"]): r for r in records}
    norm = lambda r: r["objective"] / r["mean_work"]  # noqa: E731
    out: list[str] = []

    out.append("Normalized objective J / mean truck work (mean over 5 test streams)")
    width = max(len(m) for m in METHODS) + 1
    header = f"{'size':4} {'load':4} {'demand':8}" + "".join(f"{m:>{width}}" for m in METHODS)
    out.append(header)
    for size, load, demand in CELLS:
        row = []
        for m in METHODS:
            vals = [norm(by[(m, size, load, demand, r)]) for r in SEEDS if (m, size, load, demand, r) in by]
            row.append(f"{statistics.mean(vals):{width}.3f}" if vals else f"{'-':>{width}}")
        out.append(f"{size:4} {load:<4} {demand:8}" + "".join(row))

    for ref in REFERENCES:
        out.append("")
        out.append(f"Relative to {ref} (%; mean of per-stream ratios, negative = better)")
        out.append(f"  {'':5}" + "".join(f"{m:>{width}}" for m in METHODS))
        for scope in (*SIZES, "all"):
            cells = [c for c in CELLS if scope in ("all", c[0])]
            parts = []
            for m in METHODS:
                ratios = [
                    100 * (norm(by[(m, *c, r)]) / norm(by[(ref, *c, r)]) - 1)
                    for c in cells
                    for r in SEEDS
                    if (m, *c, r) in by and (ref, *c, r) in by
                ]
                parts.append(f"{statistics.mean(ratios):+{width}.1f}" if ratios else f"{'-':>{width}}")
            out.append(f"  {scope:3}: " + "".join(parts))

    out.append("")
    for primary in ("RL-API", "Rollout"):
        out.append(f"Paired Wilcoxon (two-sided) of {primary} vs each method, per-stream J")
        for m in METHODS:
            if m == primary:
                continue
            for scope in (*SIZES, "all"):
                pairs = [
                    (norm(by[(primary, *c, r)]), norm(by[(m, *c, r)]))
                    for c in CELLS
                    if scope in ("all", c[0])
                    for r in SEEDS
                    if (primary, *c, r) in by and (m, *c, r) in by
                ]
                if len(pairs) < 6:
                    continue
                diffs = [a - b for a, b in pairs]
                wins = sum(d < 0 for d in diffs)
                p, _ = wilcoxon_signed_rank(diffs)
                out.append(f"  vs {m:19} {scope:3} n={len(pairs):3} {primary} better in {wins:3}  p={p:.2g}")
        out.append("")

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
    if BOUNDS.exists():
        lb = {(b["size"], b["load"], b["demand"], b["rep"]): b["lower_bound"] for b in
              (json.loads(line) for line in BOUNDS.read_text().splitlines() if line)}
        out.append("")
        out.append("Absolute references (per stream): gap % above the lower bound (stream_lower_bound) and above the best")
        out.append("observed method on that stream (over all methods run on it); mean over the streams that have the bound")
        out.append(f"  {'':5}" + "".join(f"{m:>{width}}" for m in METHODS))
        for kind in ("vs LB", "vs best"):
            for scope in (*SIZES, "all"):
                keys = [(*c, r) for c in CELLS if scope in ("all", c[0]) for r in SEEDS if (*c, r) in lb]
                parts = []
                for m in METHODS:
                    vals = []
                    for k in keys:
                        if (m, *k) not in by:
                            continue
                        mine = by[(m, *k)]["objective"]
                        if kind == "vs LB":
                            vals.append(100 * (mine / lb[k] - 1))
                        else:
                            best = min(by[(o, *k)]["objective"] for o in METHODS if (o, *k) in by)
                            vals.append(100 * (mine / best - 1))
                    parts.append(f"{statistics.mean(vals):+{width}.1f}" if vals else f"{'-':>{width}}")
                out.append(f"  {kind[:7]:7}{scope:3}: " + "".join(parts))
        ratios = [by[("Rollout", *k)]["objective"] / lb[k] for k in lb if ("Rollout", *k) in by]
        if ratios:
            out.append(f"  Rollout / lower bound: mean {statistics.mean(ratios):.2f}, min {min(ratios):.2f}, max {max(ratios):.2f}")

    cp = [r for r in records if r["method"] == "Cyclic-CPSAT" and "cycles" in r]
    if cp:
        out.append("")
        out.append("Cyclic-CPSAT: cycles proved optimal by CP-SAT (10 s per cycle)")
        for size in SIZES:
            rows = [r for r in cp if r["size"] == size]
            if rows:
                total = sum(r["cycles"] for r in rows)
                opt = sum(r["cpsat_optimal_cycles"] for r in rows)
                out.append(f"  {size}: {opt}/{total} ({100 * opt / total:.1f}%) over {len(rows)} streams")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="run")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--sizes", default=",".join(SIZES))
    args = parser.parse_args()
    if args.mode == "bounds":
        print(f"computed {bounds(args.workers, tuple(args.sizes.split(',')))} new bounds -> {BOUNDS}")
    elif args.mode != "summary":
        executed = run(args.workers, tuple(args.methods.split(",")), tuple(args.sizes.split(",")))
        print(f"executed {executed} new jobs -> {OUTPUT}")
    print(summarize())


if __name__ == "__main__":
    main()
