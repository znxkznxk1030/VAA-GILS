"""Approximate policy iteration: distil the rollout teacher into the dispatcher.

TRAIN pool streams are labelled by `RolloutPolicy` (one simulation-based
policy-improvement step over FCFS-VAA); the network is fitted to the labels
with DAgger (states visited by the current network are added each round).
The checkpoint is selected on the TUNING set, as for PPO.

`--oracle` uses the hindsight teacher instead (hindsight learning, Sinclair et
al. 2022): the rollout looks ahead along the stream's real future (arrivals are
exogenous, so the observed future is a valid training signal), one sample. The
learned policy itself still sees only the current state. `--soft T` trains on
the teacher's action costs (soft targets) instead of its argmax.

Usage:
    python experiments/stream_api_train.py --name api --rounds 5
    python experiments/stream_api_train.py --name api_hs --rounds 6 --oracle --samples 1
    python experiments/stream_api_train.py --name api_hs_soft --rounds 6 --oracle --samples 1 --episodes 16 --soft 0.5
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.rl import (
    DispatchNet,
    TrainConfig,
    behaviour_clone,
    collect_labels,
    collect_soft_labels,
    fit_classifier,
    fit_soft,
)
from crossdock_solver.stream.rollout import RolloutPolicy
from crossdock_solver.stream.sim import CrossDockStream
from experiments.stream_rl_train import OUT, tuning_score

TRAIN_BASE = 100_000
SIZES = ("S", "M")
LOADS = (0.5, 0.6, 0.7)
DEMANDS = ("uniform", "skewed")


def _label(job):
    episode, state, beta, samples, horizon, oracle, soft = job
    torch.set_num_threads(1)
    rng = random.Random(episode)
    size, load, demand = rng.choice(SIZES), rng.choice(LOADS), rng.choice(DEMANDS)
    env = CrossDockStream(
        stream_config(size, load=load, demand=demand),
        seed=TRAIN_BASE + 60_000 + episode,
        measure_from=50,
        measure_to=250,
    )
    net = None
    if state is not None:
        net = DispatchNet()
        net.load_state_dict(state)
        net.eval()
    teacher = RolloutPolicy(samples=samples, horizon_sla=horizon, seed=episode, oracle=oracle)
    if soft:
        return collect_soft_labels(net, teacher, env, beta=beta, rng=rng, temperature=soft)
    return collect_labels(net, teacher, env, beta=beta, rng=rng)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="api")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--episodes", type=int, default=8)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--horizon", type=float, default=1.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--oracle", action="store_true", help="hindsight teacher (real future)")
    parser.add_argument("--soft", type=float, default=0.0, help="cost-sensitive soft targets with this temperature")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    net = DispatchNet()
    behaviour_clone(net, TrainConfig(bc_episodes=16))  # start from FCFS-VAA
    best = {"score": tuning_score(net), "round": -1}
    torch.save(net.state_dict(), OUT / f"{args.name}.pt")
    print(f"round -1 (BC) tuning J/work={best['score']:.4f}", flush=True)
    log = (OUT / f"{args.name}.log.jsonl").open("w")
    dataset: list = []
    episode = 0
    for round_ in range(args.rounds):
        beta = 1.0 if round_ == 0 else 0.5
        state = None if round_ == 0 else {k: v.clone() for k, v in net.state_dict().items()}
        jobs = [(episode + e, state, beta, args.samples, args.horizon, args.oracle, args.soft) for e in range(args.episodes)]
        episode += args.episodes
        with multiprocessing.Pool(args.workers) as pool:
            for data in pool.imap_unordered(_label, jobs):
                dataset.extend(data)
        fit = fit_soft if args.soft else fit_classifier
        loss = fit(net, dataset, epochs=args.epochs, lr=1e-3, seed=round_)
        score = tuning_score(net)
        record = {"round": round_, "states": len(dataset), "loss": loss, "tuning_score": score}
        log.write(json.dumps(record) + "\n")
        log.flush()
        if score < best["score"]:
            best = {"score": score, "round": round_}
            torch.save(net.state_dict(), OUT / f"{args.name}.pt")
        print(f"round {round_} states={len(dataset)} loss={loss:.3f} tuning J/work={score:.4f} "
              f"(best {best['score']:.4f} @ {best['round']})", flush=True)
    summary = {"name": args.name, "best_round": best["round"], "best_tuning": best["score"]}
    (OUT / f"{args.name}.summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
