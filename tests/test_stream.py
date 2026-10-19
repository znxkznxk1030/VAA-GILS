from __future__ import annotations

import math
import random

import numpy as np
import pytest
import torch

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.policies import CyclicPlanPolicy, FCFSRulePolicy, SPTRulePolicy
from crossdock_solver.stream.policies import RandomPolicy as RandomDispatch
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


@pytest.mark.parametrize(
    "policy",
    [
        FCFSRulePolicy(),
        SPTRulePolicy(),
        RandomPolicy(),
        RandomDispatch(),
        CyclicPlanPolicy(iterations=20),
        CyclicPlanPolicy(iterations=20, solver="sa-rl5"),
        CyclicPlanPolicy(solver="cpsat", cpsat_time_limit=2.0),
    ],
    ids=lambda p: f"{type(p).__name__}-{p.name}",
)
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
        assert glob.shape == (14,)
        assert np.isfinite(glob).all()
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


def _advance(env, steps: int) -> None:
    policy = FCFSRulePolicy()
    for _ in range(steps):
        if env.done:
            break
        env.dispatch(*policy.act(env))


def test_fork_leaves_the_original_untouched_and_hides_the_future() -> None:
    env = _env(load=0.7)
    _advance(env, 60)
    snapshot = (env.now, env.units_in_system, env.cost_snapshot(), [t.uid for t in env.yard])
    pending_arrival = next(e[0] for e in env._events if e[2] == 0)

    sim = env.fork(seed=1, until=env.now + env.facility.sla)
    sim_arrival = next(e[0] for e in sim._events if e[2] == 0)
    policy = FCFSRulePolicy()
    while not sim.done:
        sim.dispatch(*policy.act(sim))

    assert (env.now, env.units_in_system, env.cost_snapshot(), [t.uid for t in env.yard]) == snapshot
    assert sim_arrival != pending_arrival  # the real next arrival is not reused
    other = env.fork(seed=1, until=env.now + env.facility.sla)
    while not other.done:
        other.dispatch(*policy.act(other))
    assert other.cost_snapshot() == sim.cost_snapshot()


def test_rollout_shortlist_contains_rule_action_and_hold() -> None:
    from crossdock_solver.stream.rollout import RolloutPolicy, shortlist

    env = _env()
    _advance(env, 30)
    actions = shortlist(env)
    assert FCFSRulePolicy().act(env) in actions and actions[-1] is None
    choice = RolloutPolicy(samples=2, horizon_sla=0.3).act(env)
    assert choice in actions


def test_candidate_index_round_trips() -> None:
    from crossdock_solver.stream.rl import candidate_index

    env = _env()
    rng = random.Random(0)
    while not env.done:
        candidates = env.candidates()
        action = rng.choice([*candidates, None])
        index = candidate_index(env, action)
        assert decode(env, index) == action
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)


def test_lower_bound_is_below_every_policy() -> None:
    from crossdock_solver.stream.bounds import stream_lower_bound
    from crossdock_solver.stream.policies import PriorityRulePolicy

    policies = [FCFSRulePolicy(), SPTRulePolicy(), RandomPolicy(seed=2), PriorityRulePolicy([1, 0, 5, 1, 0, 0, 1, -1, 2])]
    for load, demand in ((0.5, "uniform"), (0.7, "skewed")):
        bounds = []
        for policy in policies:
            env = _env(load=load, demand=demand)
            metrics = run_stream(env, policy)
            bound = stream_lower_bound(env)
            bounds.append(bound)
            assert 0 < bound <= metrics.objective + 1e-9
        assert max(bounds) - min(bounds) < 1e-9  # policy independent


def test_linear_policy_at_rule_indicator_reproduces_fcfs() -> None:
    from crossdock_solver.stream.rl import NUM_FEATURES, LinearScorePolicy

    weights = np.zeros(NUM_FEATURES)
    weights[23] = 1.0
    a = run_stream(_env(load=0.7), FCFSRulePolicy())
    b = run_stream(_env(load=0.7), LinearScorePolicy(weights))
    assert a.objective == pytest.approx(b.objective)


def test_oracle_fork_replays_the_real_future() -> None:
    env = _env(seed=11)
    for _ in range(30):
        env.dispatch(*FCFSRulePolicy().act(env))
    first_future = max(t.uid for t in env.in_system) + 1
    fork = env.fork(seed=0, until=env.now + 2 * env.facility.sla, oracle=True)
    while not fork.done:
        fork.dispatch(*FCFSRulePolicy().act(fork))
    while env.now < fork.now and not env.done:
        env.dispatch(*FCFSRulePolicy().act(env))
    real = {t.uid: t.arrival for t in [*env.departed, *env.in_system] if t.arrival <= fork.now}
    seen = {t.uid: t.arrival for t in [*fork.departed, *fork.in_system]}
    assert all(seen[uid] == pytest.approx(arrival) for uid, arrival in real.items() if uid in seen)
    assert sum(uid >= first_future for uid in set(real) & set(seen)) >= 5  # future trucks reproduced


def test_hindsight_model_matches_simulator_and_bounds_policies() -> None:
    from crossdock_solver.stream.finite import FiniteStream, sample_finite_instance
    from crossdock_solver.stream.hindsight import evaluate_schedule, schedule_of, solve_hindsight
    from crossdock_solver.stream.rollout import RolloutPolicy

    instance = sample_finite_instance(stream_config("S", load=0.6), seed=7, n=4)
    values = []
    for policy in (FCFSRulePolicy(), RandomDispatch(seed=1), RolloutPolicy(samples=1, oracle=True)):
        env = FiniteStream(instance)
        metrics = run_stream(env, policy)
        assert metrics.undelivered_units == 0
        assert evaluate_schedule(instance, schedule_of(env)).objective == pytest.approx(metrics.objective, abs=1e-6)
        values.append(metrics.objective)
    best = solve_hindsight(instance, time_limit=60, workers=4)
    relaxed = solve_hindsight(instance, time_limit=60, workers=4, relax_doors=True)
    assert relaxed.bound <= best.objective + 1e-6
    assert best.objective <= min(values) + 1e-6


def test_finite_forks_know_the_shift_length_and_sweep() -> None:
    from crossdock_solver.stream.finite import FiniteStream, sample_finite_instance

    instance = sample_finite_instance(stream_config("S", load=0.6), seed=5, n=8)
    env = FiniteStream(instance)
    env.dispatch(*FCFSRulePolicy().act(env))
    fork = env.fork(seed=3, until=1e9)
    while not fork.done:
        fork.dispatch(*FCFSRulePolicy().act(fork))
    assert fork._arrivals == 8  # resampled future, but no truck beyond the shift
    assert not any(fork.open_lots)  # stranded freight went to the sweeper
    assert fork.units_in_system == pytest.approx(0.0)


def test_rolling_horizon_conserves_freight() -> None:
    from crossdock_solver.stream.rolling import RollingHorizonPolicy

    env = CrossDockStream(stream_config("S", load=0.6), seed=4, measure_from=10, measure_to=40)
    policy = RollingHorizonPolicy(time_limit=0.2)
    metrics = run_stream(env, policy)
    assert metrics.undelivered_units == 0
    assert env.units_in_system >= 0
    assert policy.solves > 0
