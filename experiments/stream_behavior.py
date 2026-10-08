"""What does the learned dispatcher do differently from FCFS-VAA? (TUNING set)

Per policy: door time blocked while carriers wait for freight, share of
decisions that hold / skip the head-of-yard truck / deviate from the rule's
destination, and how closely carrier frequency tracks freight volume per
destination (L1 distance between the two shares).

Usage:
    python experiments/stream_behavior.py
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.policies import CyclicPlanPolicy, FCFSRulePolicy
from crossdock_solver.stream.rl import DispatchNet, RLPolicy
from crossdock_solver.stream.sim import CrossDockStream
from experiments.stream_rl_train import OUT, TUNING_BASE, TUNING_SET


def profile(policy, size, load, demand, seed):
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=seed, measure_from=100, measure_to=500)
    rule = FCFSRulePolicy()
    if hasattr(policy, "reset"):
        policy.reset(env)
    decisions = holds = skip_head = other_dest = 0
    while not env.done:
        reference = rule.act(env)
        action = policy.act(env)
        decisions += 1
        if action is None:
            holds += 1
            env.hold()
            continue
        if action[0] is not env.yard[0]:
            skip_head += 1
        elif action[2] != reference[2]:
            other_dest += 1
        env.dispatch(*action)
    busy = blocked = 0.0
    carriers = np.zeros(env.config.num_destinations)
    units = np.zeros(env.config.num_destinations)
    for t in env.departed:
        busy += t.departure - t.dock_time
        load_start = t.departure - t.leave - sum(l.handling for l in t.lots)
        blocked += max(0.0, load_start - t.claim_time)
        carriers[t.destination] += 1
        units[t.destination] += t.carried_units
    m = env.metrics()
    return {
        "J/work": m.objective / env.facility.mean_work,
        "blocked%": 100 * blocked / busy,
        "hold%": 100 * holds / decisions,
        "skip_head%": 100 * skip_head / decisions,
        "other_dest%": 100 * other_dest / decisions,
        "freq_gap": float(np.abs(carriers / carriers.sum() - units / units.sum()).sum()),
        "empty_out%": 100 * m.empty_outbound_rate,
        "yard_wait/work": m.mean_yard_wait / env.facility.mean_work,
    }


def main() -> None:
    torch.set_num_threads(1)
    api = DispatchNet()
    api.load_state_dict(torch.load(OUT / "api.pt"))
    policies = {
        "FCFS-VAA": lambda: FCFSRulePolicy(),
        "Cyclic-VAA": lambda: CyclicPlanPolicy(iterations=0),
        "RL-API": lambda: RLPolicy(api, name="RL-API"),
    }
    for demand in ("uniform", "skewed"):
        print(f"demand={demand}")
        for name, make in policies.items():
            rows = [
                profile(make(), size, load, d, TUNING_BASE + k)
                for k, (size, load, d) in enumerate(TUNING_SET)
                if d == demand
            ]
            keys = rows[0].keys()
            print(f"  {name:11} " + "  ".join(f"{k}={np.mean([r[k] for r in rows]):.3f}" for k in keys))


if __name__ == "__main__":
    main()
