"""Tune the linear priority rule (PriorityRulePolicy) by the cross-entropy method.

Protocol (same pools as the RL policies):
- the search objective is the mean J/work over 36 TRAIN-pool streams
  (S/M x load 0.5/0.6/0.7 x uniform/skewed x 3 seeds, seeds 180000+, trucks 100..399),
- the final rule is chosen among the last elites and the best-so-far by the
  TUNING-set score (the same 12 streams used to select the RL checkpoints),
- the TEST pool is never touched here.

Parameters: 9 feature weights (crossdock_solver.stream.policies.PRIORITY_FEATURES)
and a hold threshold. The search starts near FCFS-Backlog (large weight on the
yard wait, own-freight share and backlog) with no holding.

`--kind linear24` instead tunes a linear score over the 24 candidate features of
the RL network (LinearScorePolicy, HOLD included), starting exactly at FCFS-VAA:
the same-information linear baseline for the learned policies.

Usage:
    python experiments/stream_rule_tune.py --workers 7
    python experiments/stream_rule_tune.py --workers 7 --kind linear24 --name tuned_linear
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
from crossdock_solver.stream.policies import PRIORITY_FEATURES, PriorityRulePolicy
from crossdock_solver.stream.sim import CrossDockStream, run_stream


OUT = ROOT / "outputs" / "stream_rl"
TRAIN_BASE = 180_000
TUNING_BASE = 200_000
TRAIN_REPS = 3
CELLS = [(s, l, d) for s in ("S", "M") for l in (0.5, 0.6, 0.7) for d in ("uniform", "skewed")]
INIT_MEAN = np.array([5.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -30.0])  # weights..., threshold
INIT_STD = np.array([2.0] * len(PRIORITY_FEATURES) + [10.0])
KIND = "priority"


def _linear_init() -> tuple[np.ndarray, np.ndarray]:
    from crossdock_solver.stream.rl import NUM_FEATURES

    mean = np.zeros(NUM_FEATURES)
    mean[23] = 1.0  # rule indicator -> FCFS-VAA
    return mean, np.full(NUM_FEATURES, 0.5)


def make_policy(params: np.ndarray):
    if KIND == "linear24":
        from crossdock_solver.stream.rl import LinearScorePolicy

        return LinearScorePolicy(params)
    return PriorityRulePolicy(params[:-1], params[-1])


def score(params: np.ndarray, pool: str) -> float:
    policy = make_policy(params)
    values = []
    for k, (size, load, demand) in enumerate(CELLS):
        if pool == "train":
            # time_cap_factor 3 (default 20) cuts off policies whose queue explodes; their
            # censored cost is still far worse than any reasonable rule
            envs = [CrossDockStream(stream_config(size, load=load, demand=demand), seed=TRAIN_BASE + 100 * k + rep,
                                    measure_from=100, measure_to=400, time_cap_factor=3.0) for rep in range(TRAIN_REPS)]
        else:  # tuning set, identical to experiments/stream_rl_train.tuning_score
            envs = [CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k,
                                    measure_from=100, measure_to=500)]
        for env in envs:
            metrics = run_stream(env, policy)
            values.append(metrics.objective / env.facility.mean_work)
    return float(np.mean(values))


def _init_worker(kind: str) -> None:
    global KIND
    KIND = kind


def _train_score(params) -> float:
    return score(np.asarray(params), "train")


def _tuning_score(params) -> float:
    return score(np.asarray(params), "tuning")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--population", type=int, default=64)
    parser.add_argument("--elite", type=int, default=10)
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--name", default="tuned_rule")
    parser.add_argument("--kind", choices=("priority", "linear24"), default="priority")
    parser.add_argument("--resume", help="log.jsonl of an interrupted run: start from its last mean/std")
    args = parser.parse_args()
    _init_worker(args.kind)

    rng = np.random.default_rng(args.seed)
    if args.kind == "linear24":
        mean, std = _linear_init()
    else:
        mean, std = INIT_MEAN.copy(), INIT_STD.copy()
    floor = 0.05 * std
    if args.resume:
        last = [json.loads(line) for line in Path(args.resume).read_text().splitlines() if line][-1]
        mean, std = np.array(last["mean"]), np.array(last["std"])
        print(f"resumed from {args.resume} iteration {last['iteration']}", flush=True)
    log_path = OUT / f"{args.name}.log.jsonl"
    best_params, best_value = mean.copy(), np.inf
    start = time.time()
    with multiprocessing.Pool(args.workers, initializer=_init_worker, initargs=(args.kind,)) as pool, log_path.open("w", encoding="utf-8") as log:
        base = pool.apply(_train_score, (mean,))
        print(f"init train J/work={base:.4f}", flush=True)
        for it in range(args.iterations):
            samples = mean + std * rng.standard_normal((args.population, len(mean)))
            samples[0] = mean  # keep the current mean in the population
            values = np.array(pool.map(_train_score, list(samples)))
            order = np.argsort(values)
            elite = samples[order[: args.elite]]
            if values[order[0]] < best_value:
                best_value, best_params = float(values[order[0]]), samples[order[0]].copy()
            mean = elite.mean(axis=0)
            std = np.maximum(elite.std(axis=0), floor)
            record = {"iteration": it, "best": float(values[order[0]]), "elite_mean": float(values[order[: args.elite]].mean()),
                      "best_so_far": best_value, "mean": mean.tolist(), "std": std.tolist(), "elapsed": time.time() - start}
            log.write(json.dumps(record) + "\n")
            log.flush()
            print(f"it {it:2d} best={values[order[0]]:.4f} elite={record['elite_mean']:.4f} so_far={best_value:.4f} "
                  f"({record['elapsed']:.0f}s)", flush=True)

        candidates = [mean, best_params, *elite[:4]]
        tuning = pool.map(_tuning_score, candidates)
    pick = int(np.argmin(tuning))
    chosen = candidates[pick]
    summary = {
        "kind": args.kind,
        "features": list(PRIORITY_FEATURES) if args.kind == "priority" else "rl.candidate_features (24)",
        "weights": (chosen[:-1] if args.kind == "priority" else chosen).tolist(),
        "threshold": float(chosen[-1]) if args.kind == "priority" else None,
        "train_score": _train_score(chosen),
        "tuning_score": float(tuning[pick]),
        "tuning_scores_candidates": [float(v) for v in tuning],
        "init_train_score": base,
    }
    (OUT / f"{args.name}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
