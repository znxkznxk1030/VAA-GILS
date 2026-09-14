"""Budget-fairness check: SA-RL5 baselines given the same wall-clock time as GILS.

GILS runs a best-improvement descent after improving moves, so 1,000 iterations
of GILS cost more time than 1,000 iterations of SA-RL5. For every test run in the
main search batch (sizes S/M/L x TW none/medium/tight, instances 0-19, reps 0-4)
the SA-RL5 baseline receives exactly the runtime that v2-GILS-uniform-1000 used
on that (instance, rep) and iterates until the time is spent. Paper-SA-RL5 is
used on TW none, Extended-SA-RL5 on medium/tight, as in the main comparison.

Run alone (no other experiments in parallel): the budgets are wall-clock times.

Usage:
    python experiments/budget_fairness.py          # run missing jobs, then summarize
    python experiments/budget_fairness.py summary  # summarize only
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.k1_stats import wilcoxon_signed_rank
from experiments.runner import Job, run_jobs


K1 = ROOT / "outputs" / "k1_results.jsonl"
OUTPUT = ROOT / "outputs" / "budget_fairness.jsonl"
SIZES = ("S", "M", "L")
TW_LEVELS = (None, "medium", "tight")
INDICES = tuple(range(20))
REPS = tuple(range(5))
GILS = "v2-GILS-uniform-1000"


def _baselines(tw: str | None) -> tuple[str, str]:
    """(iteration-matched, time-matched) SA-RL5 method for a TW level."""

    if tw is None:
        return "Paper-SA-RL5-1000", "Paper-SA-RL5-timematch"
    return "Extended-SA-RL5-1000", "Extended-SA-RL5-timematch"


def _objective(record: dict) -> float:
    """Paper-SA-RL5 records (TW none) store only makespan, which is the objective there."""

    return record.get("objective", record.get("makespan"))


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def fairness_jobs() -> list[Job]:
    runtime = {
        (r["size_class"], r["tw_tightness"], r["index"], r["rep"]): r["runtime_sec"]
        for r in _load(K1)
        if r["method"] == GILS
    }
    jobs: list[Job] = []
    for size in SIZES:
        for tw in TW_LEVELS:
            for index in INDICES:
                for rep in REPS:
                    jobs.append(
                        Job(
                            method=_baselines(tw)[1],
                            pool="test",
                            size_class=size,
                            flow_pattern="uniform",
                            tw_tightness=tw,
                            index=index,
                            rep=rep,
                            budget_sec=runtime[(size, tw, index, rep)],
                        )
                    )
    return jobs


def summarize() -> None:
    runs: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for r in _load(K1) + _load(OUTPUT):
        if r["pool"] != "test" or r["index"] >= 20:
            continue
        key = (r["size_class"], r["tw_tightness"], r["index"], r["rep"])
        runs[key][r["method"]] = r

    def instance_diffs(size_filter, baseline_of):
        """Per-instance mean relative gap (baseline - GILS) / GILS * 100."""

        per_instance: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
        for (size, tw, index, rep), methods in runs.items():
            if size not in size_filter:
                continue
            base = baseline_of(tw)
            if GILS in methods and base in methods:
                per_instance[(size, tw, index)]["g"].append(_objective(methods[GILS]))
                per_instance[(size, tw, index)]["b"].append(_objective(methods[base]))
        diffs = []
        for values in per_instance.values():
            g, b = statistics.mean(values["g"]), statistics.mean(values["b"])
            diffs.append(100.0 * (b - g) / g)
        return diffs

    def mean_field(size_filter, method_of, field):
        values = [
            methods[method_of(tw)][field]
            for (size, tw, index, rep), methods in runs.items()
            if size in size_filter and method_of(tw) in methods and field in methods[method_of(tw)]
        ]
        return statistics.mean(values) if values else float("nan")

    print("GILS-uniform-1000 vs SA-RL5 baselines (positive = GILS better; instance-level Wilcoxon)")
    print(
        f"{'size':<5}{'n':>4}{'vs 1000 it.':>13}{'p':>9}{'vs time-matched':>17}{'p':>9}"
        f"{'GILS s':>9}{'SA-1000 s':>11}{'SA-time s':>11}{'SA-time it.':>13}"
    )
    for label, sizes in (("S", {"S"}), ("M", {"M"}), ("L", {"L"}), ("all", set(SIZES))):
        d_iter = instance_diffs(sizes, lambda tw: _baselines(tw)[0])
        d_time = instance_diffs(sizes, lambda tw: _baselines(tw)[1])
        if not d_time:
            continue
        p_iter, _ = wilcoxon_signed_rank(d_iter)
        p_time, n = wilcoxon_signed_rank(d_time)
        print(
            f"{label:<5}{n:>4}{statistics.mean(d_iter):>+13.3f}{p_iter:>9.2g}"
            f"{statistics.mean(d_time):>+17.3f}{p_time:>9.2g}"
            f"{mean_field(sizes, lambda tw: GILS, 'runtime_sec'):>9.2f}"
            f"{mean_field(sizes, lambda tw: _baselines(tw)[0], 'runtime_sec'):>11.2f}"
            f"{mean_field(sizes, lambda tw: _baselines(tw)[1], 'runtime_sec'):>11.2f}"
            f"{mean_field(sizes, lambda tw: _baselines(tw)[1], 'iterations'):>13.0f}"
        )
    worse = [d for d in instance_diffs(set(SIZES), lambda tw: _baselines(tw)[1]) if d < 0]
    print(f"instances where time-matched SA-RL5 beats GILS: {len(worse)}")


def main() -> None:
    if sys.argv[1:] != ["summary"]:
        executed = run_jobs(fairness_jobs(), OUTPUT, workers=6)
        print(f"budget fairness: executed {executed} new jobs -> {OUTPUT}")
    summarize()


if __name__ == "__main__":
    main()
