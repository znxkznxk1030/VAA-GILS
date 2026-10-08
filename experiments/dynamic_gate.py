"""G0: headroom gate for the dynamic-arrival study (TUNING pool only).

Before any learning is attempted, measure how far the non-learning online
policies are from the clairvoyant hindsight solution. If certainty-equivalent
re-optimization (Rolling-GILS) is already within a few tenths of a percent of
hindsight, a learned policy has no room to help and the information model has
to change before RL work starts.

Grid: S/M x TW none/medium/tight x uncertainty low/medium/high, 5 tuning
instances x 2 arrival realizations per cell. Methods: Random, StaticPlan,
Greedy, Rolling-GILS and Hindsight (GILS-1000 on the realized instance).

Usage:
    python experiments/dynamic_gate.py          # run missing jobs, then summarize
    python experiments/dynamic_gate.py summary  # summarize only
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import multiprocessing
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.dynamic.policies import (
    GreedyRepairPolicy,
    RandomPolicy,
    RollingGILSPolicy,
    StaticPlanPolicy,
    hindsight,
    run_episode,
)
from crossdock_solver.dynamic.scenario import UNCERTAINTY_LEVELS, make_scenario
from experiments.protocol import BenchmarkCell, cell_instance, cell_seed


OUTPUT = ROOT / "outputs" / "dynamic_gate.jsonl"
POOL = "tuning"
SIZES = ("S", "M")
TW_LEVELS = (None, "medium", "tight")
LEVELS = tuple(UNCERTAINTY_LEVELS)
INDICES = range(5)
REALIZATIONS = range(2)
METHODS = ("Random", "StaticPlan", "Greedy", "Rolling-GILS", "Hindsight")


@dataclass(frozen=True)
class DynJob:
    method: str
    size_class: str
    tw_tightness: str | None
    level: str
    index: int
    realization: int

    @property
    def key(self) -> str:
        tw = self.tw_tightness or "none"
        return (
            f"{self.method}|{POOL}|{self.size_class}|{tw}|{self.level}"
            f"|{self.index}|{self.realization}"
        )


def scenario_seed(cell: BenchmarkCell, index: int, level: str, realization: int) -> int:
    return cell_seed(POOL, cell, index) * 100 + LEVELS.index(level) * 10 + realization


def _policy(method: str, seed: int):
    if method == "Random":
        return RandomPolicy(seed=seed)
    if method == "StaticPlan":
        return StaticPlanPolicy(iterations=1000, seed=seed)
    if method == "Greedy":
        return GreedyRepairPolicy(iterations=1000, seed=seed)
    if method == "Rolling-GILS":
        return RollingGILSPolicy(iterations=200, initial_iterations=1000, seed=seed)
    raise ValueError(method)


def _execute(job: DynJob) -> dict:
    cell = BenchmarkCell(job.size_class, "uniform", job.tw_tightness)
    planned = cell_instance(POOL, cell, job.index)
    seed = scenario_seed(cell, job.index, job.level, job.realization)
    scenario = make_scenario(planned, job.level, seed=seed)
    if job.method == "Hindsight":
        result = hindsight(scenario, iterations=1000, seed=seed)
    else:
        result = run_episode(scenario, _policy(job.method, seed))
    return {
        "key": job.key,
        "method": job.method,
        "size_class": job.size_class,
        "tw": job.tw_tightness or "none",
        "level": job.level,
        "index": job.index,
        "realization": job.realization,
        "objective": result.objective,
        "makespan": result.makespan,
        "total_tardiness": result.total_tardiness,
        "plan_sec": result.plan_sec,
        "decide_sec_total": result.decide_sec_total,
        "decide_sec_max": result.decide_sec_max,
        "num_decisions": len(planned.all_trucks),
    }


def jobs() -> list[DynJob]:
    return [
        DynJob(method, size, tw, level, index, realization)
        for size in SIZES
        for tw in TW_LEVELS
        for level in LEVELS
        for index in INDICES
        for realization in REALIZATIONS
        for method in METHODS
    ]


def run(workers: int = 6) -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    pending = [job for job in jobs() if job.key not in done]
    if not pending:
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("a", encoding="utf-8") as sink, multiprocessing.Pool(workers) as pool:
        for record in pool.imap_unordered(_execute, pending):
            sink.write(json.dumps(record) + "\n")
            sink.flush()
    return len(pending)


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    by_scenario: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in records:
        scenario = (r["size_class"], r["tw"], r["level"], r["index"], r["realization"])
        by_scenario[scenario][r["method"]] = r

    gaps: dict[tuple, list[float]] = defaultdict(list)
    latency: dict[tuple, list[float]] = defaultdict(list)
    for (size, tw, level, _, _), methods in by_scenario.items():
        if "Hindsight" not in methods:
            continue
        reference = methods["Hindsight"]["objective"]
        for method, r in methods.items():
            if method == "Hindsight":
                continue
            gap = 100.0 * (r["objective"] - reference) / reference
            for key in ((size, tw, level, method), (size, "*", level, method), ("*", "*", level, method)):
                gaps[key].append(gap)
            latency[(size, method)].append(r["decide_sec_total"] / r["num_decisions"])

    online = [m for m in METHODS if m != "Hindsight"]
    lines = ["Mean gap to Hindsight (%), per cell [n scenarios]", ""]
    header = f"{'size':4} {'tw':6} {'level':6} " + " ".join(f"{m:>12}" for m in online)
    lines.append(header)
    for size in (*SIZES, "*"):
        for tw in ((*[t or "none" for t in TW_LEVELS], "*") if size != "*" else ("*",)):
            for level in LEVELS:
                row = [gaps.get((size, tw, level, m)) for m in online]
                if not any(row):
                    continue
                cells = " ".join(
                    f"{statistics.mean(v):12.2f}" if v else f"{'-':>12}" for v in row
                )
                n = len(row[0]) if row[0] else 0
                lines.append(f"{size:4} {tw:6} {level:6} {cells}  [{n}]")
        lines.append("")
    lines.append("Mean online decision latency (ms per decision)")
    for size in SIZES:
        cells = " ".join(
            f"{m}={1000 * statistics.mean(latency[(size, m)]):.2f}"
            for m in online
            if latency.get((size, m))
        )
        lines.append(f"  {size}: {cells}")
    return "\n".join(lines)


def main() -> None:
    if sys.argv[1:] != ["summary"]:
        executed = run()
        print(f"executed {executed} new jobs -> {OUTPUT}")
    print(summarize())


if __name__ == "__main__":
    main()
