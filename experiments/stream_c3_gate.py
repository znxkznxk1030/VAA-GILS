"""C3 gate: does time-varying destination demand + forecast information + the
carrier claim decision leave room that one-step look-ahead can use?

Stage 1 of the C3 design (docs/c3_gate_design.md). Rollout only, no learning.
S, load 0.7, skewed demand, 12 streams of a fresh C3 tuning pool (seeds
600000+), measurement window trucks 100-500.

Factors
    A    : wave amplitude of the total rate and of the destination shares (0, 0.6)
    info : what the look-ahead samples its future from
           I0 long-run averages, I2 true curves, I3 the real future (oracle)
    ext  : claim decision off (0) or on (up to 4 extensions of 0.25 mean work)

Gate (judged on the means of the paired per-stream ratios)
    G1 information : (J_I0 - J_I3) / J_I0 at A=0.6 >= 2 x the same at A=0
                     (the stationary value of information, about 4% in 5.6)
    G2 action      : (J_ext0 - J_ext4) / J_ext0 of Rollout-I2 at A=0.6 >= 3%
    pass if G1 or G2; otherwise C3 stops.

Usage:
    python experiments/stream_c3_gate.py --workers 4
    python experiments/stream_c3_gate.py --summary
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
from crossdock_solver.stream.demand import demand_model
from crossdock_solver.stream.policies import FCFSRulePolicy
from crossdock_solver.stream.rollout import RolloutPolicy
from crossdock_solver.stream.sim import CrossDockStream, run_stream

OUTPUT = ROOT / "outputs" / "stream_c3_gate.jsonl"
SUMMARY = ROOT / "outputs" / "stream_c3_gate_summary.txt"
C3_BASE = 600_000
STREAMS = 12
SIZE, LOAD, DEMAND = "S", 0.7, "skewed"
EXTENSIONS = 4

# (method, A, info, ext); info is None for FCFS-VAA (no look-ahead)
CONFIGS = [
    ("FCFS-VAA", 0.0, None, 0),
    ("FCFS-VAA", 0.6, None, 0),
    ("Rollout", 0.0, "I2", 0),
    ("Rollout", 0.0, "I2", EXTENSIONS),
    ("Rollout", 0.0, "I3", 0),
    ("Rollout", 0.0, "I3", EXTENSIONS),
    ("Rollout", 0.6, "I0", 0),
    ("Rollout", 0.6, "I2", 0),
    ("Rollout", 0.6, "I3", 0),
    ("Rollout", 0.6, "I0", EXTENSIONS),
    ("Rollout", 0.6, "I2", EXTENSIONS),
    ("Rollout", 0.6, "I3", EXTENSIONS),
]


def label(method: str, amplitude: float, info: str | None, ext: int) -> str:
    if info is None:
        return f"{method} A={amplitude}"
    return f"{method}-{info} A={amplitude} ext={ext}"


def make_env(amplitude: float, ext: int, rep: int) -> CrossDockStream:
    config = stream_config(SIZE, load=LOAD, demand=DEMAND, amplitude=amplitude, dest_amplitude=amplitude,
                           max_extensions=ext)
    return CrossDockStream(config, seed=C3_BASE + rep, measure_from=100, measure_to=500)


def _job(job: tuple) -> dict:
    (method, amplitude, info, ext), rep = job
    env = make_env(amplitude, ext, rep)
    if info is None:
        policy = FCFSRulePolicy()
    elif info == "I3":
        policy = RolloutPolicy(oracle=True)
    else:
        policy = RolloutPolicy(demand=demand_model(info, env.facility))
    start = time.perf_counter()
    metrics = run_stream(env, policy)
    seconds = time.perf_counter() - start
    carriers = [t for t in env.departed if t.uid >= 0 and env.measure_from <= t.uid < env.measure_to]
    return {
        "method": method, "amplitude": amplitude, "info": info, "ext": ext, "rep": rep,
        "score": metrics.objective / env.facility.mean_work,
        **metrics.as_dict(),
        "mean_work": env.facility.mean_work,
        "extension_rate": float(np.mean([t.extensions > 0 for t in carriers])) if carriers else 0.0,
        "mean_extensions": float(np.mean([t.extensions for t in carriers])) if carriers else 0.0,
        "units_per_carrier": float(np.mean([t.carried_units for t in carriers])) if carriers else 0.0,
        "door_time": float(np.mean([t.departure - t.dock_time for t in carriers])) / env.facility.mean_work
        if carriers else 0.0,
        "seconds": seconds,
    }


def run(workers: int) -> None:
    done = set()
    if OUTPUT.exists():
        for line in OUTPUT.read_text().splitlines():
            r = json.loads(line)
            done.add((r["method"], r["amplitude"], r["info"], r["ext"], r["rep"]))
    jobs = [(c, rep) for c in CONFIGS for rep in range(STREAMS) if (*c, rep) not in done]
    # cheap jobs first so partial results are usable early
    jobs.sort(key=lambda j: (j[0][2] not in (None, "I3"), j[0][1], j[1]))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with multiprocessing.Pool(workers) as pool, OUTPUT.open("a") as sink:
        for row in pool.imap_unordered(_job, jobs):
            sink.write(json.dumps(row) + "\n")
            sink.flush()
            print(f"{label(row['method'], row['amplitude'], row['info'], row['ext']):28} rep {row['rep']:2} "
                  f"J/work {row['score']:.3f} ({row['seconds']:.0f}s)", flush=True)


def summarize() -> str:
    from scipy.stats import wilcoxon

    rows = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    by = {(r["method"], r["amplitude"], r["info"], r["ext"], r["rep"]): r for r in rows}

    def scores(config) -> np.ndarray | None:
        vals = [by.get((*config, rep)) for rep in range(STREAMS)]
        if any(v is None for v in vals):
            return None
        return np.array([v["score"] for v in vals])

    out = [f"C3 gate: {SIZE}, load {LOAD}, {DEMAND}, {STREAMS} streams (seeds {C3_BASE}+), J / mean truck work", ""]
    out.append(f"{'config':30} {'J/work':>7} {'vs FCFS':>8} {'ext rate':>8} {'ext/carrier':>11} "
               f"{'units/carrier':>13} {'door time':>9} {'s/stream':>8}")
    for config in CONFIGS:
        vals = [by.get((*config, rep)) for rep in range(STREAMS)]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        fcfs = scores(("FCFS-VAA", config[1], None, 0))
        mean = lambda k: float(np.mean([v[k] for v in vals]))  # noqa: E731
        rel = "" if fcfs is None or len(vals) < STREAMS else f"{np.mean(scores(config) / fcfs - 1):+8.1%}"
        out.append(f"{label(*config):30} {mean('score'):7.3f} {rel:>8} {mean('extension_rate'):8.2f} "
                   f"{mean('mean_extensions'):11.2f} {mean('units_per_carrier'):13.1f} {mean('door_time'):9.2f} "
                   f"{mean('seconds'):8.0f}" + ("" if len(vals) == STREAMS else f"  ({len(vals)}/{STREAMS})"))

    def gain(worse, better, name: str):
        a, b = scores(worse), scores(better)
        if a is None or b is None:
            out.append(f"{name}: incomplete")
            return None
        rel = 1 - b / a
        p = wilcoxon(a, b).pvalue if np.any(a != b) else 1.0
        out.append(f"{name}: {np.mean(rel):+.1%} (better in {int(np.sum(b < a))}/{STREAMS}, Wilcoxon p = {p:.2g})")
        return float(np.mean(rel))

    out += ["", "Gains (1 - J_better / J_worse, mean over streams)"]
    v0 = gain(("Rollout", 0.0, "I2", 0), ("Rollout", 0.0, "I3", 0), "info I0/I2 -> I3, A=0   (stationary VoI)")
    v6 = gain(("Rollout", 0.6, "I0", 0), ("Rollout", 0.6, "I3", 0), "info I0 -> I3, A=0.6")
    gain(("Rollout", 0.6, "I0", 0), ("Rollout", 0.6, "I2", 0), "info I0 -> I2, A=0.6     (knowing the curves)")
    gain(("Rollout", 0.6, "I2", 0), ("Rollout", 0.6, "I3", 0), "info I2 -> I3, A=0.6     (knowing the realization)")
    gain(("Rollout", 0.0, "I2", 0), ("Rollout", 0.0, "I2", EXTENSIONS), "claim decision, A=0, I2")
    g2 = gain(("Rollout", 0.6, "I2", 0), ("Rollout", 0.6, "I2", EXTENSIONS), "claim decision, A=0.6, I2")
    gain(("Rollout", 0.6, "I0", 0), ("Rollout", 0.6, "I0", EXTENSIONS), "claim decision, A=0.6, I0")
    gain(("Rollout", 0.6, "I3", 0), ("Rollout", 0.6, "I3", EXTENSIONS), "claim decision, A=0.6, I3")
    gain(("Rollout", 0.6, "I0", EXTENSIONS), ("Rollout", 0.6, "I2", EXTENSIONS), "info I0 -> I2 with claim decision, A=0.6")

    out += ["", "Gate"]
    if v0 is None or v6 is None or g2 is None:
        out.append("incomplete")
    else:
        g1_pass = v6 >= 2 * v0
        g2_pass = g2 >= 0.03
        out.append(f"G1 information: {v6:+.1%} vs 2 x {v0:+.1%} -> {'pass' if g1_pass else 'fail'}")
        out.append(f"G2 claim decision: {g2:+.1%} vs +3.0% -> {'pass' if g2_pass else 'fail'}")
        out.append(f"=> {'PASS: continue C3' if g1_pass or g2_pass else 'FAIL: stop C3'}")
    text = "\n".join(out)
    SUMMARY.write_text(text + "\n")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    if not args.summary:
        run(args.workers)
    print(summarize())


if __name__ == "__main__":
    main()
