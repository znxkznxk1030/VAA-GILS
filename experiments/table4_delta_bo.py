"""Reproduce the columns of the paper's Table 4 from outputs/k1_results.jsonl.

For every condition (size x time-window level) and every method in Table 4 it
prints the mean objective, the sample standard deviation over all runs, the
gap to the best observed solution (Delta_bo, Eq. (20)-(21) of the paper) and
the gap to the CP-SAT reference (vs CP-SAT).

Definitions
    J_bo(pi)       minimum objective over every run recorded for instance pi in
                   k1_results.jsonl: all methods, all selection policies and
                   iteration budgets, and CP-SAT (Eq. (20)).
    Delta_bo(a)    mean over instances of the mean over method a's runs of
                   100 * (J(x) - J_bo(pi)) / J_bo(pi)  (Eq. (21)). VAA is
                   deterministic and has one run per instance; the other
                   methods have five.
    vs CP-SAT(a)   the same formula with the CP-SAT reference objective in place
                   of J_bo, over the instances that have a CP-SAT reference. For
                   S this is the 300 s run in k1_results.jsonl; for M it is the
                   600 s rerun in cpsat_rerun.jsonl (L has no feasible reference).

Usage:
    python experiments/table4_delta_bo.py
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "outputs" / "k1_results.jsonl"
CPSAT_RERUN = ROOT / "outputs" / "cpsat_rerun.jsonl"
TABLE4_METHODS = (
    ("VAA", "VAA"),
    ("Paper-SA-RL5", "Paper-SA-RL5-1000"),
    ("Extended-SA-RL5", "Extended-SA-RL5-1000"),
    ("GILS-uniform", "v2-GILS-uniform-1000"),
)
SIZES = ("S", "M", "L")
TW_LEVELS = ("none", "medium", "tight")


def _objective(record: dict) -> float | None:
    return record.get("objective", record.get("makespan"))


def _instance(record: dict) -> tuple[str, str, int]:
    return (record["size_class"], record.get("tw_tightness") or "none", record["index"])


def _mean_relative_gap(runs: dict[tuple, list[float]], reference: dict[tuple, float]) -> float | None:
    """Mean over instances of the mean relative gap (%) of their runs to the reference."""

    per_instance = [
        statistics.mean(100.0 * (value - reference[key]) / reference[key] for value in values)
        for key, values in runs.items()
        if key in reference
    ]
    return statistics.mean(per_instance) if per_instance else None


def main() -> None:
    records = [json.loads(line) for line in RESULTS.read_text().splitlines() if line.strip()]

    best_observed: dict[tuple, float] = {}
    cpsat_reference: dict[tuple, float] = {}
    runs: dict[str, dict[tuple, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        value = _objective(record)
        if value is None:
            continue
        key = _instance(record)
        best_observed[key] = min(best_observed.get(key, value), value)
        if record["method"].startswith("CPSAT"):
            cpsat_reference[key] = value
        runs[record["method"]][key].append(value)

    # The M references in Table 4 come from the CP-SAT rerun; they never improve on
    # the best observed value, but they are included in J_bo for completeness.
    for line in CPSAT_RERUN.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        value = record.get("objective")
        if value is None:
            continue
        key = _instance(record)
        best_observed[key] = min(best_observed.get(key, value), value)
        cpsat_reference[key] = value

    print(f"{'condition':<10}{'method':<17}{'mean obj.':>11}{'s.d.':>10}{'Δbo(%)':>9}{'vs CP-SAT(%)':>14}{'runs':>6}")
    for size in SIZES:
        for tw in TW_LEVELS:
            for label, method in TABLE4_METHODS:
                cell = {k: v for k, v in runs[method].items() if k[0] == size and k[1] == tw}
                if not cell:
                    continue
                values = [value for values in cell.values() for value in values]
                gap_bo = _mean_relative_gap(cell, best_observed)
                gap_cp = _mean_relative_gap(cell, cpsat_reference)
                cp_text = f"{gap_cp:+.2f}" if gap_cp is not None else "---"
                print(
                    f"{size}-{tw:<8}{label:<17}{statistics.mean(values):>11.1f}"
                    f"{statistics.stdev(values):>10.1f}{gap_bo:>9.2f}{cp_text:>14}{len(values):>6}"
                )


if __name__ == "__main__":
    main()
