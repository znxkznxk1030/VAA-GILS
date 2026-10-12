"""Cycle-level solution quality of the static methods inside the continuous cross-dock.

Cyclic planning turns every |D| arriving trucks into a static instance
(|I_c| + |F_c| = |D|). This script harvests such cycle instances from TUNING-pool
streams (seeds 250000+, never the test pool) and solves each one with

    VAA, SA-RL5 (original paper, 1,000 iterations, objective with tardiness),
    VAA-GILS (1,000 iterations, final engine), CP-SAT (60 s, optimality proof)

so the stream results can be read against the static ordering of the JKIIE
study: does a better cycle solution translate into a better stream?

Usage:
    python experiments/stream_cycle_quality.py            # run + summarize
    python experiments/stream_cycle_quality.py summary
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.baselines.paper_sa_rl import PaperSARLConfig, run_paper_sa_rl
from crossdock_solver.baselines.vaa import vaa_solution
from crossdock_solver.baselines.vaa_qrl import ACTIONS_TW, VaaQRLConfig, run_vaa_qrl
from crossdock_solver.core.evaluator import evaluate_solution
from crossdock_solver.exact.cpsat import ExactCPSATConfig, solve_exact_cpsat
from crossdock_solver.rl.selectors import UniformSelector
from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.policies import CyclicPlanPolicy
from crossdock_solver.stream.sim import CrossDockStream, run_stream
from experiments.k1_stats import wilcoxon_signed_rank


OUTPUT = ROOT / "outputs" / "stream_cycle_quality.jsonl"
SEED_BASE = 250_000  # tuning pool, disjoint from the PPO/API tuning set (200000-200011)
SIZES = ("S", "M", "L")
LOADS = (0.5, 0.6, 0.7)
DEMANDS = ("uniform", "skewed")
CELLS = [(s, l, d) for s in SIZES for l in LOADS for d in DEMANDS]
FIRST_CYCLE, STRIDE, PER_STREAM = 20, 3, 8
METHODS = ("VAA", "SA-RL5", "GILS")


class _Harvest(CyclicPlanPolicy):
    """Cyclic-VAA that records the static instance of selected cycles."""

    def __init__(self) -> None:
        super().__init__(iterations=0)
        self.captured: list[tuple[int, object, float]] = []

    def _solve(self, instance, weight):
        k = self._cycle
        if k >= FIRST_CYCLE and (k - FIRST_CYCLE) % STRIDE == 0 and len(self.captured) < PER_STREAM:
            self.captured.append((k, instance, weight))
        return super()._solve(instance, weight)


def harvest(cell: tuple, rep: int = 0) -> list[tuple[int, object, float]]:
    size, load, demand = cell
    cfg = stream_config(size, load=load, demand=demand)
    trucks = (FIRST_CYCLE + STRIDE * PER_STREAM + 2) * cfg.num_destinations
    env = CrossDockStream(cfg, seed=SEED_BASE + 1_000 * CELLS.index(cell) + rep, measure_from=0, measure_to=trucks)
    policy = _Harvest()
    run_stream(env, policy)
    return policy.captured


def solve_cycle(instance, weight: float, seed: int) -> dict:
    score = lambda r: r.makespan + weight * r.total_tardiness  # noqa: E731
    out: dict = {"compounds": len(instance.compound_trucks), "outbounds": len(instance.outbound_trucks)}
    start = time.perf_counter()
    out["VAA"] = score(evaluate_solution(instance, vaa_solution(instance)))
    out["VAA_sec"] = time.perf_counter() - start
    run = run_paper_sa_rl(
        instance, PaperSARLConfig(max_iterations=1000, tardiness_weight=weight, seed=seed, name="Extended-SA-RL5")
    )
    out["SA-RL5"], out["SA-RL5_sec"] = score(run.result), run.runtime_sec
    run = run_vaa_qrl(
        instance,
        VaaQRLConfig(max_iterations=1000, tardiness_weight=weight, seed=seed, use_sa_acceptance=False),
        selector=UniformSelector(ACTIONS_TW),
    )
    out["GILS"], out["GILS_sec"] = score(run.result), run.runtime_sec
    exact = solve_exact_cpsat(instance, ExactCPSATConfig(time_limit_sec=60.0, workers=1, tardiness_weight=weight))
    out["CPSAT"], out["CPSAT_sec"], out["CPSAT_optimal"] = exact.objective_value, exact.runtime_sec, exact.proven_optimal
    return out


def run() -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    executed = 0
    with OUTPUT.open("a", encoding="utf-8") as sink:
        for cell in CELLS:
            if all(f"{'|'.join(map(str, cell))}|{FIRST_CYCLE + STRIDE * i}" in done for i in range(PER_STREAM)):
                continue
            for k, instance, weight in harvest(cell):
                key = f"{'|'.join(map(str, cell))}|{k}"
                if key in done:
                    continue
                record = {"key": key, "size": cell[0], "load": cell[1], "demand": cell[2], "cycle": k}
                record.update(solve_cycle(instance, weight, seed=k))
                sink.write(json.dumps(record) + "\n")
                sink.flush()
                executed += 1
                print(f"{key} VAA={record['VAA']:.1f} SA-RL5={record['SA-RL5']:.1f} GILS={record['GILS']:.1f} "
                      f"CPSAT={record['CPSAT']} opt={record['CPSAT_optimal']} ({record['CPSAT_sec']:.1f}s)", flush=True)
    return executed


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    out = ["Cycle-level quality (tuning-pool streams; gap % to the CP-SAT solution of the same cycle)"]
    out.append(f"{'scope':6}{'n':>5}{'opt':>6}" + "".join(f"{m + ' gap':>13}{m + ' max':>12}{m + '=opt':>11}" for m in METHODS)
               + f"{'CP-SAT s':>10}{'SA-RL5 ms':>11}{'GILS ms':>9}")
    for scope in (*SIZES, "all"):
        rows = [r for r in records if scope in ("all", r["size"]) and r["CPSAT"] is not None]
        if not rows:
            continue
        line = f"{scope:6}{len(rows):5d}{sum(r['CPSAT_optimal'] for r in rows):6d}"
        for m in METHODS:
            gaps = [100 * (r[m] / r["CPSAT"] - 1) for r in rows]
            hits = sum(g < 1e-6 for g in gaps)
            line += f"{statistics.mean(gaps):13.2f}{max(gaps):12.2f}{100 * hits / len(rows):10.0f}%"
        line += f"{statistics.mean(r['CPSAT_sec'] for r in rows):10.2f}"
        line += f"{1000 * statistics.mean(r['SA-RL5_sec'] for r in rows):11.0f}"
        line += f"{1000 * statistics.mean(r['GILS_sec'] for r in rows):9.0f}"
        out.append(line)
    out.append("")
    out.append("Paired Wilcoxon (two-sided) of GILS vs SA-RL5, cycle objective")
    for scope in (*SIZES, "all"):
        rows = [r for r in records if scope in ("all", r["size"])]
        diffs = [r["GILS"] - r["SA-RL5"] for r in rows]
        p, _ = wilcoxon_signed_rank(diffs)
        out.append(f"  {scope:3} n={len(rows):3} GILS better {sum(d < 0 for d in diffs):3}  tie {sum(d == 0 for d in diffs):3}"
                   f"  SA-RL5 better {sum(d > 0 for d in diffs):3}  p={p:.2g}")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="run")
    args = parser.parse_args()
    if args.mode != "summary":
        print(f"executed {run()} new cycles -> {OUTPUT}")
    print(summarize())


if __name__ == "__main__":
    main()
