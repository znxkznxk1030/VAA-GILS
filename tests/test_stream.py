from __future__ import annotations

import math
import random

import numpy as np
import pytest
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.policies import CyclicPlanPolicy, FCFSRulePolicy
from crossdock_solver.stream.rl import (
    DispatchNet,
    RLPolicy,
    candidate_features,
    decode,
    rule_index,
)
from crossdock_solver.stream.sim import CrossDockStream, run_stream


def _env(load: float = 0.6, demand: str = "uniform", seed: int = 3, **kwargs) -> CrossDockStream:
    return CrossDockStream(stream_config("S", load=load, demand=demand), seed=seed, measure_from=20, measure_to=120, **kwargs)


class RandomPolicy:
    name = "random"

    def __init__(self, seed: int = 0, hold_prob: float = 0.1) -> None:
        self.rng = random.Random(seed)
        self.hold_prob = hold_prob

    def act(self, env):
        if self.rng.random() < self.hold_prob:
            return None
        return self.rng.choice(env.candidates())


@pytest.mark.parametrize("policy", [FCFSRulePolicy(), RandomPolicy(), CyclicPlanPolicy(iterations=20)], ids=lambda p: p.name)
def test_freight_is_conserved_and_delivered(policy) -> None:
    env = _env()
    metrics = run_stream(env, policy)
    assert metrics.undelivered_units == 0
    arrived = sum(t.units.sum() for t in env.in_system) + sum(t.units.sum() for t in env.departed)
    carried = sum(t.carried_units for t in env.departed)
    assert env.units_in_system == pytest.approx(arrived - carried)
    for truck in env.departed:
        assert truck.departure >= truck.dock_time >= truck.arrival
        for lot in truck.lots:
            assert lot.destination == truck.destination
            assert truck.departure >= lot.ready + env.facility.travel[lot.door, truck.door]


def test_doors_never_serve_two_trucks_at_once() -> None:
    env = _env(load=0.7)
    run_stream(env, RandomPolicy(seed=5))
    by_door: dict[int, list] = {}
    for truck in env.departed:
        by_door.setdefault(truck.door, []).append((truck.dock_time, truck.departure))
    for intervals in by_door.values():
        intervals.sort()
        for (_, end), (start, _) in zip(intervals, intervals[1:]):
            assert start >= end - 1e-9


def test_policies_see_only_arrived_trucks() -> None:
    env = _env()
    policy = FCFSRulePolicy()
    while not env.done:
        assert all(t.arrival <= env.now for t in env.yard)
        assert all(not math.isnan(t.dock_time) or t in env.yard for t in env.in_system)
        env.dispatch(*policy.act(env))


def test_cost_accrual_matches_departure_metrics_for_tardiness() -> None:
    env = CrossDockStream(stream_config("S", load=0.7), seed=9, measure_from=0, measure_to=150)
    run_stream(env, FCFSRulePolicy())
    exact = sum(max(0.0, t.departure - t.due) for t in env.departed)
    pending = sum(max(0.0, env.now - t.due) for t in env.in_system)
    assert env.tardy_integral == pytest.approx(exact + pending, rel=1e-9, abs=1e-6)


def test_candidate_features_align_with_candidates() -> None:
    env = _env()
    steps = 0
    while not env.done and steps < 200:
        feats, glob = candidate_features(env)
        candidates = env.candidates()
        assert feats.shape == (len(candidates) + 1, 24)
        assert glob.shape == (4,)
        assert np.isfinite(feats).all()
        index = rule_index(env)
        assert feats[index, 23] == 1.0 and feats[:, 23].sum() == 1.0
        assert decode(env, index) == FCFSRulePolicy().act(env)
        env.dispatch(*decode(env, index))
        steps += 1


def test_rl_policy_runs_on_unseen_size() -> None:
    torch.manual_seed(0)
    env = CrossDockStream(stream_config("L", load=0.5), seed=4, measure_from=10, measure_to=60)
    metrics = run_stream(env, RLPolicy(DispatchNet(), sample=True))
    assert metrics.trucks == 50
