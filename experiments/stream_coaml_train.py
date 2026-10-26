"""Optimization-augmented policy: rolling CP-SAT with a learned terminal delay.

1. collect: RL-API runs on TRAIN-pool streams (seeds 140000+, never used by the
   other trainings) give (state, destination) -> realized wait for the next
   out-of-model carrier (crossdock_solver.stream.terminal),
2. fit: TerminalNet (Huber regression), 20% of the streams held out,
3. tune: the rolling policy with the learned delay (times `--scales`) on the
   TUNING set (same 12 streams and 1 s CP-SAT as stream_rolling_tune.py), so it
   is comparable with the tuned constant (outputs/stream_rl/rolling.json).

Usage:
    python experiments/stream_coaml_train.py --workers 7
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.sim import CrossDockStream, run_stream

OUT = ROOT / "outputs" / "stream_rl"
COLLECT_BASE = 140_000
TUNING_BASE = 200_000
CELLS = [(s, l, d) for s in ("S", "M") for l in (0.5, 0.6, 0.7) for d in ("uniform", "skewed")]
REPS = 3
TIME_LIMIT = 1.0


def _collect(job):
    from crossdock_solver.stream.terminal import collect_terminal_labels
    from experiments.stream_eval import _policy

    torch.set_num_threads(1)
    k, rep = job
    size, load, demand = CELLS[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=COLLECT_BASE + 100 * k + rep,
                          measure_from=50, measure_to=450)
    return k, rep, collect_terminal_labels(env, _policy("RL-API"))


def _tune(job):
    from crossdock_solver.stream.rolling import RollingHorizonPolicy
    from crossdock_solver.stream.terminal import LearnedTerminal, TerminalNet

    torch.set_num_threads(1)
    scale, k = job
    net = TerminalNet()
    net.load_state_dict(torch.load(OUT / "terminal.pt"))
    size, load, demand = CELLS[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k,
                          measure_from=100, measure_to=500)
    policy = RollingHorizonPolicy(time_limit=TIME_LIMIT, terminal_model=LearnedTerminal(net, scale))
    metrics = run_stream(env, policy)
    return {"scale": scale, "cell": k, "score": metrics.objective / env.facility.mean_work,
            "solves": policy.solves, "fallbacks": policy.fallbacks}


def main() -> None:
    from crossdock_solver.stream.terminal import TerminalNet, fit_terminal

    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--scales", default="1.0")
    args = parser.parse_args()

    jobs = [(k, rep) for k in range(len(CELLS)) for rep in range(REPS)]
    with multiprocessing.Pool(args.workers) as pool:
        collected = pool.map(_collect, jobs)
    train = [x for k, rep, data in collected if rep != 0 for x in data]
    held = [x for k, rep, data in collected if rep == 0 for x in data]

    torch.manual_seed(0)
    net = TerminalNet()
    loss = fit_terminal(net, train)
    torch.save(net.state_dict(), OUT / "terminal.pt")

    def _mae(data, predict):
        errs = []
        for feats, label, valid in data:
            if valid.any():
                errs.extend(np.abs(predict(feats)[valid] - label[valid]))
        return float(np.mean(errs))

    with torch.no_grad():
        learned = _mae(held, lambda f: net(torch.from_numpy(f)).numpy())
    labels = np.concatenate([y[v] for _, y, v in train])
    constant = _mae(held, lambda f: np.full(len(f), float(np.median(labels))))
    fit = {"train_states": len(train), "held_states": len(held), "loss": loss,
           "held_mae_learned": learned, "held_mae_median_constant": constant,
           "label_mean": float(labels.mean()), "label_median": float(np.median(labels))}
    print(json.dumps(fit), flush=True)

    scales = [float(x) for x in args.scales.split(",")]
    tune_jobs = [(s, k) for s in scales for k in range(len(CELLS))]
    rows = []
    with multiprocessing.Pool(args.workers) as pool, (OUT / "coaml_tune.jsonl").open("w") as sink:
        for row in pool.imap_unordered(_tune, tune_jobs):
            rows.append(row)
            sink.write(json.dumps(row) + "\n")
            sink.flush()
    scores = {s: float(np.mean([r["score"] for r in rows if r["scale"] == s])) for s in scales}
    best = min(scores, key=scores.get)
    summary = {"fit": fit, "scale": best, "time_limit": TIME_LIMIT, "tuning_scores": scores,
               "constant_rolling_tuning": json.loads((OUT / "rolling.json").read_text())["tuning_scores"]}
    (OUT / "coaml.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
