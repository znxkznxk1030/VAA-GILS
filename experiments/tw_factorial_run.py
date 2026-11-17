"""Factorial experiment on the two time-constraint factors (reviewer comment R1-13).

The main experiments use only two (rho, delta) combinations, (0.25, 0.60) and
(0.50, 0.35), so the release spread and the due-date slack change together.
This script crosses four levels of each factor, including "off":

    rho   (release spread, r_q ~ U[0, rho*H])      in {0 (all trucks at time 0), 0.10, 0.25, 0.50}
    delta (due-date slack, d_q = r_q + delta*H)    in {inf (no due dates), 1.00, 0.60, 0.35}

(rho, delta) = (0, inf) is the original setting without time constraints. The
row rho = 0 adds due dates only and the column delta = inf adds release times
only, so each factor can also be examined alone. With delta = inf the
objective is the makespan (tardiness weight 0), as in the "none" condition.

The same base instance (flows, handling times, door layout, enter/leave times)
and the same uniform draws u_q are used in all sixteen cells of an instance, i.e.
r_q = u_q * rho * H. Only rho and delta differ between cells, so differences
between cells are paired by instance.

Instances use a dedicated seed range (400,000+), disjoint from the train,
tuning and test pools. Methods and hyperparameters are the frozen ones.

Usage:
    python experiments/tw_factorial_run.py
"""

from __future__ import annotations

from dataclasses import replace
import json
import multiprocessing
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.data.generator import _makespan_estimate, generate_benchmark_instance
from experiments.methods import METHOD_REGISTRY

OUTPUT = ROOT / "outputs" / "tw_factorial.jsonl"

SIZES = ("S", "M", "L")
RHOS = (0.0, 0.10, 0.25, 0.50)
DELTAS = (float("inf"), 1.00, 0.60, 0.35)
INDICES = tuple(range(20))
REPS = tuple(range(5))
METHODS = ("VAA", "Extended-SA-RL5-1000", "v2-GILS-uniform-1000")
SEED_BASE = 400_000


def instance_seed(size: str, index: int) -> int:
    return SEED_BASE + SIZES.index(size) * 1_000 + index


def build_instance(size: str, index: int, rho: float, delta: float):
    seed = instance_seed(size, index)
    base = generate_benchmark_instance(size, "uniform", seed=seed, tw_tightness=None)
    horizon = _makespan_estimate(base.flow, base.product_time, len(base.doors))
    draws = random.Random(seed * 7 + 1)
    u = {truck: draws.random() for truck in base.all_trucks}
    release = {truck: round(u[truck] * rho * horizon, 1) for truck in base.all_trucks}
    if delta == float("inf"):
        due = {truck: float("inf") for truck in base.all_trucks}
    else:
        due = {truck: round(release[truck] + delta * horizon, 1) for truck in base.all_trucks}
    return replace(base, release_time=release, due_time=due), horizon


def all_jobs() -> list[tuple]:
    jobs = []
    for size in SIZES:
        for index in INDICES:
            for rho in RHOS:
                for delta in DELTAS:
                    for method in METHODS:
                        for rep in ((0,) if method == "VAA" else REPS):
                            jobs.append((method, size, index, rho, delta, rep))
    return jobs


def key_of(job: tuple) -> str:
    method, size, index, rho, delta, rep = job
    return f"{method}|factorial|{size}|{rho:.2f}|{delta:.2f}|{index}|{rep}"


def execute(job: tuple) -> dict:
    method, size, index, rho, delta, rep = job
    instance, horizon = build_instance(size, index, rho, delta)
    seed = instance_seed(size, index)
    result = METHOD_REGISTRY[method](instance, seed * 100 + rep, None)
    return {
        "key": key_of(job),
        "method": method,
        "size_class": size,
        "index": index,
        "rho": rho,
        "delta": delta,
        "rep": rep,
        "instance_seed": seed,
        "horizon": horizon,
        "finished_at": time.time(),
        **result,
    }


def main() -> None:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line.strip()}
    pending = [job for job in all_jobs() if key_of(job) not in done]
    print(f"tw_factorial: {len(pending)} pending of {len(all_jobs())}", flush=True)
    if not pending:
        return
    with OUTPUT.open("a", encoding="utf-8") as sink, multiprocessing.Pool(6) as pool:
        for record in pool.imap_unordered(execute, pending, chunksize=4):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    print(f"tw_factorial: done -> {OUTPUT}")


if __name__ == "__main__":
    main()
