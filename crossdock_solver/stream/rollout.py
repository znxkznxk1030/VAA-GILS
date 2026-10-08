"""Simulation-based policy improvement (rollout) for the continuous cross-dock.

At each decision a short list of candidate actions is scored by simulating
the next `horizon_sla * SLA` time units from a fork of the current state
(future arrivals resampled, common random numbers across candidates) with
the base policy taking every later decision. The candidate with the lowest
accrued cost is executed. This is one policy-improvement step of approximate
policy iteration; `distill` in `rl.py` turns its decisions into a fast
network policy.
"""

from __future__ import annotations

import numpy as np

from crossdock_solver.stream.policies import (
    FCFSRulePolicy,
    backlog_handling,
    central_door,
    nearest_door_to_lots,
)
from crossdock_solver.stream.sim import CrossDockStream


def rule_door(env: CrossDockStream, truck, destination: int, doors: list[int]) -> int:
    if truck.compound:
        return central_door(env, doors)
    return nearest_door_to_lots(env, doors, destination)


def shortlist(env: CrossDockStream, extra_trucks: int = 2) -> list:
    """Head truck with every destination, the rule action of the next trucks, HOLD."""

    doors = env.free_doors()
    head = env.yard[0]
    actions: list = [
        (head, rule_door(env, head, d, doors), d) for d in range(env.config.num_destinations)
    ]
    rule = FCFSRulePolicy()
    waiting = backlog_handling(env)
    for truck in env.yard[1 : 1 + extra_trucks]:
        d = int(np.argmax(truck.handling)) if truck.compound else int(np.argmax(waiting))
        actions.append((truck, rule_door(env, truck, d, doors), d))
    actions.append(None)
    # the rule action is always the head truck's entry for its rule destination
    assert rule.act(env) in actions
    return actions


class RolloutPolicy:
    def __init__(
        self,
        base=None,
        *,
        samples: int = 8,
        horizon_sla: float = 1.0,
        extra_trucks: int = 2,
        seed: int = 0,
        name: str = "Rollout",
    ) -> None:
        self.base = base or FCFSRulePolicy()
        self.samples = samples
        self.horizon_sla = horizon_sla
        self.extra_trucks = extra_trucks
        self.seed = seed
        self.name = name
        self._step = 0

    def reset(self, env: CrossDockStream) -> None:
        self._step = 0

    def scores(self, env: CrossDockStream, actions: list) -> np.ndarray:
        until = env.now + self.horizon_sla * env.facility.sla
        totals = np.zeros(len(actions))
        for r in range(self.samples):
            seed = (self.seed * 1_000_003 + self._step * 7_919 + r) & 0x7FFFFFFF
            for i, action in enumerate(actions):
                sim = env.fork(seed, until)
                start = sim.cost_snapshot()
                if action is None:
                    sim.hold()
                else:
                    truck, door, destination = action
                    sim.dispatch(sim.truck_by_uid(truck.uid), door, destination)
                while not sim.done:
                    sim.dispatch(*self.base.act(sim))
                totals[i] += sim.cost_snapshot() - start
        return totals / self.samples

    def act(self, env: CrossDockStream):
        actions = shortlist(env, self.extra_trucks)
        best = actions[int(np.argmin(self.scores(env, actions)))]
        self._step += 1
        return best
