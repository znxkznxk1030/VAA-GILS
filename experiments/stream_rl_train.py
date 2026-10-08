"""Train the RL dispatcher for the continuous cross-dock (TRAIN pool seeds).

Checkpoint selection uses the TUNING pool only: every `--eval-every`
iterations the greedy policy is run on a fixed tuning set and the checkpoint
with the lowest mean normalized objective (J / mean truck work) is kept.

Usage:
    python experiments/stream_rl_train.py --name ppo_bc            # BC warm start + PPO
    python experiments/stream_rl_train.py --name ppo_scratch --no-bc
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.rl import RLPolicy, TrainConfig, train
from crossdock_solver.stream.sim import CrossDockStream, run_stream


OUT = ROOT / "outputs" / "stream_rl"
TUNING_BASE = 200_000
TUNING_SET = [
    (size, load, demand)
    for size in ("S", "M")
    for load in (0.5, 0.6, 0.7)
    for demand in ("uniform", "skewed")
]


def tuning_score(net) -> float:
    scores = []
    for k, (size, load, demand) in enumerate(TUNING_SET):
        env = CrossDockStream(
            stream_config(size, load=load, demand=demand),
            seed=TUNING_BASE + k,
            measure_from=100,
            measure_to=500,
        )
        metrics = run_stream(env, RLPolicy(net))
        scores.append(metrics.objective / env.facility.mean_work)
    return float(np.mean(scores))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--eval-every", type=int, default=20)
    parser.add_argument("--no-bc", action="store_true")
    parser.add_argument("--entropy", type=float, default=0.0)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--clip", type=float, default=0.1)
    parser.add_argument("--critic-warmup", type=int, default=10)
    parser.add_argument("--tau-sla", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    log_path = OUT / f"{args.name}.log.jsonl"
    log = log_path.open("w", encoding="utf-8")
    cfg = TrainConfig(
        iterations=args.iterations,
        episodes_per_iter=args.episodes,
        bc_episodes=0 if args.no_bc else 16,
        entropy=args.entropy,
        lr=args.lr,
        clip=args.clip,
        critic_warmup=args.critic_warmup,
        tau_sla=args.tau_sla,
        seed=args.seed,
        measure_from=100,
        measure_to=400,
    )
    best = {"score": float("inf"), "iteration": -1, "state": None}

    def callback(iteration: int, net) -> None:
        record = dict(cfg.log[-1])
        if iteration % args.eval_every == args.eval_every - 1 or iteration == args.iterations - 1:
            score = tuning_score(net)
            record["tuning_score"] = score
            if score < best["score"]:
                best.update(score=score, iteration=iteration, state=copy.deepcopy(net.state_dict()))
                torch.save(best["state"], OUT / f"{args.name}.pt")
            print(f"  tuning J/work={score:.4f} (best {best['score']:.4f} @ {best['iteration']})", flush=True)
        log.write(json.dumps(record) + "\n")
        log.flush()

    def progress(message: str) -> None:
        print(message, flush=True)

    net = train(cfg, progress=progress, callback=callback)
    if best["state"] is None:
        torch.save(net.state_dict(), OUT / f"{args.name}.pt")
    # BC-only reference: score of the warm start before PPO is logged separately.
    summary = {"name": args.name, "best_iteration": best["iteration"], "best_tuning": best["score"], "no_bc": args.no_bc}
    (OUT / f"{args.name}.summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
