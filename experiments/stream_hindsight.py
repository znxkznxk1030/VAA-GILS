"""Hindsight benchmark on short finite truck sets (S facility).

Each instance is the first n trucks of a stream from the HINDSIGHT pool
(seeds 500000+, never used for training, tuning or the stream test grid),
started empty, with the terminal sweeper rule of `crossdock_solver.stream.finite`.

Per instance:
- every online policy is run in the simulator (`FiniteStream`); the CP-SAT model
  re-evaluates its schedule and must reproduce the simulator objective,
- HS-event: CP-SAT with dock times restricted to arrival/departure times, i.e.
  the action space of the online policies with perfect information. Its
  incumbent is a realizable schedule (upper reference); hinted with the best
  policy schedule,
- HS-free: CP-SAT with free dock times (a relaxation of HS-event), hinted with
  the HS-event incumbent. Its proven optimum or bound is a lower reference for
  every policy.

Usage:
    python experiments/stream_hindsight.py                # run missing instances + summarize
    python experiments/stream_hindsight.py summary
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.finite import FiniteStream, sample_finite_instance
from crossdock_solver.stream.hindsight import evaluate_schedule, schedule_of, solve_hindsight
from crossdock_solver.stream.sim import run_stream
from experiments.k1_stats import wilcoxon_signed_rank

OUTPUT = ROOT / "outputs" / "stream_hindsight.jsonl"
SUMMARY = ROOT / "outputs" / "stream_hindsight_summary.txt"
HINDSIGHT_BASE = 500_000
LOADS = (0.5, 0.6, 0.7)
DEMANDS = ("uniform", "skewed")
CELLS = [(l, d) for l in LOADS for d in DEMANDS]
PLAN = {6: (5, 300.0), 10: (2, 600.0)}  # n -> (instances per cell, CP-SAT seconds per solve)
POLICIES = ("FCFS-VAA", "SPT-VAA", "Tuned-Rule", "Tuned-Linear", "RL-API", "Rollout", "Rollout-32", "Rollout-Oracle")
ONLINE = tuple(p for p in POLICIES if p != "Rollout-Oracle")


def _seed(n: int, cell: tuple, rep: int) -> int:
    return HINDSIGHT_BASE + 10_000 * n + 100 * CELLS.index(cell) + rep


def run_instance(n: int, load: float, demand: str, rep: int, time_limit: float, workers: int) -> dict:
    from experiments.stream_eval import _policy

    seed = _seed(n, (load, demand), rep)
    instance = sample_finite_instance(stream_config("S", load=load, demand=demand), seed, n)
    record = {"key": f"{n}|{load}|{demand}|{rep}", "n": n, "load": load, "demand": demand, "rep": rep, "seed": seed,
              "compound": sum(t.compound for t in instance.trucks), "policies": {}}
    schedules = {}
    for name in POLICIES:
        env = FiniteStream(instance)
        metrics = run_stream(env, _policy(name))
        schedule = schedule_of(env)
        check = evaluate_schedule(instance, schedule).objective
        if abs(check - metrics.objective) > 1e-6:
            raise AssertionError(f"model {check} != simulator {metrics.objective} for {name} on {record['key']}")
        record["policies"][name] = {"objective": metrics.objective,
                                    "sweeps": sum(1 for t in env.departed if t.uid < 0)}
        schedules[name] = schedule
    best = min(ONLINE, key=lambda p: record["policies"][p]["objective"])
    event = solve_hindsight(instance, time_limit=time_limit, workers=workers, hint=schedules[best], event_aligned=True)
    hint = {"dock": event.dock, "door": event.door, "destination": event.destination} if event.dock else schedules[best]
    free = solve_hindsight(instance, time_limit=time_limit, workers=workers, hint=hint)
    for label, result in (("hs_event", event), ("hs_free", free)):
        record[label] = {"objective": result.objective, "bound": result.bound, "optimal": result.optimal,
                         "status": result.status, "seconds": result.seconds}
    return record


def run(workers: int, sizes: tuple[int, ...]) -> int:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["key"] for line in OUTPUT.read_text().splitlines() if line}
    count = 0
    with OUTPUT.open("a", encoding="utf-8") as sink:
        for n in sizes:
            reps, time_limit = PLAN[n]
            for rep in range(reps):
                for load, demand in CELLS:
                    if f"{n}|{load}|{demand}|{rep}" in done:
                        continue
                    record = run_instance(n, load, demand, rep, time_limit, workers)
                    sink.write(json.dumps(record) + "\n")
                    sink.flush()
                    count += 1
                    print(f"{record['key']}: best online {min(record['policies'][p]['objective'] for p in ONLINE):.2f} "
                          f"HS-event {record['hs_event']['objective']:.2f} HS-free {record['hs_free']['objective']:.2f}"
                          f"/{record['hs_free']['bound']:.2f} ({record['hs_free']['status']})", flush=True)
    return count


def summarize() -> str:
    records = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    out = ["Hindsight benchmark (S facility, finite truck sets from the hindsight pool, empty start, terminal sweeper)",
           "gap % = 100 * (policy / reference - 1), mean over instances",
           "  HS-event = best realizable perfect-information schedule found (policy action space)",
           "  HS-free* = proven optimum / CP-SAT bound of the free-timing relaxation (valid lower reference)", ""]
    for n in sorted({r["n"] for r in records}):
        rows = [r for r in records if r["n"] == n]
        ev_opt = sum(r["hs_event"]["optimal"] for r in rows)
        fr_opt = sum(r["hs_free"]["optimal"] for r in rows)
        out.append(f"n = {n} trucks: {len(rows)} instances; HS-event proved optimal {ev_opt}, HS-free proved optimal {fr_opt}")
        lower = lambda r: r["hs_free"]["bound"]  # noqa: E731  (= optimum when proved)
        width = 15
        out.append(f"  {'':16}{'vs HS-event':>{width}}{'vs HS-free LB':>{width}}{'beats HS-event':>{width}}")
        for p in POLICIES:
            g_ev = [100 * (r["policies"][p]["objective"] / r["hs_event"]["objective"] - 1) for r in rows]
            g_lb = [100 * (r["policies"][p]["objective"] / lower(r) - 1) for r in rows if lower(r) > 0]
            wins = sum(r["policies"][p]["objective"] < r["hs_event"]["objective"] - 1e-9 for r in rows)
            out.append(f"  {p:16}{statistics.mean(g_ev):>+{width}.1f}{statistics.mean(g_lb) if g_lb else float('nan'):>+{width}.1f}"
                       f"{wins:>{width}}")
        g = [100 * (r["hs_event"]["objective"] / lower(r) - 1) for r in rows if lower(r) > 0]
        out.append(f"  {'HS-event':16}{0.0:>+{width}.1f}{statistics.mean(g):>+{width}.1f}")
        g = [100 * (r["hs_free"]["objective"] / r["hs_event"]["objective"] - 1) for r in rows]
        out.append(f"  {'HS-free (inc.)':16}{statistics.mean(g):>+{width}.1f}")
        # decomposition on the rollout family
        for a, b in (("FCFS-VAA", "Rollout"), ("Rollout", "Rollout-32"), ("Rollout", "Rollout-Oracle"), ("Rollout-Oracle", None)):
            if b is None:
                diffs = [r["policies"][a]["objective"] - r["hs_event"]["objective"] for r in rows]
                label = f"{a} - HS-event"
            else:
                diffs = [r["policies"][b]["objective"] - r["policies"][a]["objective"] for r in rows]
                label = f"{b} - {a}"
            p, _ = wilcoxon_signed_rank(diffs)
            base = statistics.mean(r["hs_event"]["objective"] for r in rows)
            out.append(f"  {label:28} mean {statistics.mean(diffs):+8.2f} ({100 * statistics.mean(diffs) / base:+.1f}% of HS-event)"
                       f"  negative in {sum(d < 0 for d in diffs)}/{len(diffs)}  p={p:.2g}")
        for load in LOADS:
            sub = [r for r in rows if r["load"] == load]
            if sub:
                parts = " ".join(
                    f"{p}={statistics.mean(100 * (r['policies'][p]['objective'] / r['hs_event']['objective'] - 1) for r in sub):+.1f}"
                    for p in ("FCFS-VAA", "RL-API", "Rollout", "Rollout-Oracle"))
                out.append(f"  load {load}: vs HS-event {parts}")
        secs = [r["hs_free"]["seconds"] for r in rows if r["hs_free"]["optimal"]]
        if secs:
            out.append(f"  HS-free proof time: mean {statistics.mean(secs):.0f}s, max {max(secs):.0f}s")
        out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="run")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--sizes", default="6,10")
    args = parser.parse_args()
    if args.mode != "summary":
        print(f"ran {run(args.workers, tuple(int(x) for x in args.sizes.split(',')))} new instances -> {OUTPUT}")
    text = summarize()
    SUMMARY.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
