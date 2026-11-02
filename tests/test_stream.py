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


# ------------------------------------------------------------ C3 gate: demand waves and claim decision
def _c3_env(seed: int = 3, measure_to: int = 120, **kwargs) -> CrossDockStream:
    config = stream_config("S", load=0.7, demand="skewed", **kwargs)
    return CrossDockStream(config, seed=seed, measure_from=20, measure_to=measure_to)


class _AlwaysExtend(FCFSRulePolicy):
    def claim(self, env, truck) -> bool:
        return True


def test_true_demand_waves_keep_shares_and_mean_rate() -> None:
    from crossdock_solver.stream.demand import TrueDemand

    env = _c3_env(amplitude=0.6, dest_amplitude=0.6)
    demand = TrueDemand(env.facility)
    grid = np.linspace(0, demand.period, 400, endpoint=False)
    weights = np.array([demand.weights(t) for t in grid])
    assert np.allclose(weights.sum(axis=1), env.config.num_destinations)
    assert np.ptp(weights, axis=0).min() > 0.3  # every destination share moves
    rates = np.array([demand.rate(t) for t in grid])
    assert rates.mean() == pytest.approx(env.facility.arrival_rate, rel=1e-6)
    assert rates.max() <= demand.rate_max + 1e-12
    # staggered: destinations peak at different times
    assert len(set(np.argmax(weights, axis=0))) == env.config.num_destinations


def test_nonstationary_arrivals_follow_the_rate_curve() -> None:
    from crossdock_solver.stream.demand import TrueDemand

    env = _c3_env(amplitude=0.6, measure_to=3000)
    demand = TrueDemand(env.facility)
    while not env.done:
        step_policy = FCFSRulePolicy()
        env.dispatch(*step_policy.act(env))
    arrivals = np.array(sorted(t.arrival for t in env.departed if t.uid >= 0))
    phase = (2 * np.pi * arrivals / demand.period + env.facility.phase[0]) % (2 * np.pi)
    high = np.sum(phase < np.pi)  # sin > 0 half of each period
    low = np.sum(phase >= np.pi)
    # expected ratio (1 + 2A/pi) / (1 - 2A/pi) = 2.23 for A = 0.6
    assert 1.9 < high / low < 2.6


def test_stationary_model_fork_matches_default_fork() -> None:
    from crossdock_solver.stream.demand import StationaryDemand

    env = _c3_env()
    _advance(env, 30)
    until = env.now + env.facility.sla
    costs = []
    for demand in (None, StationaryDemand(env.facility)):
        sim = env.fork(seed=4, until=until, demand=demand)
        while not sim.done:
            sim.dispatch(*FCFSRulePolicy().act(sim))
        costs.append(sim.cost_snapshot())
    assert costs[0] == costs[1]


def test_noisy_forecast_is_fixed_per_seed_and_unbiased() -> None:
    from crossdock_solver.stream.demand import NoisyDemand, TrueDemand

    env = _c3_env(amplitude=0.3, dest_amplitude=0.3)
    true = TrueDemand(env.facility)
    a, b = NoisyDemand(true, 0.3, seed=1), NoisyDemand(true, 0.3, seed=1)
    grid = np.linspace(0, 400 * env.facility.mean_work, 4000)
    ra = np.array([a.rate(t) for t in grid])
    assert np.array_equal(ra, [b.rate(t) for t in grid])
    ratio = ra / np.array([true.rate(t) for t in grid])
    assert ratio.std() > 0.1 and abs(ratio.mean() - 1) < 0.1
    assert np.allclose(np.array([a.weights(t) for t in grid[:50]]).sum(axis=1), env.config.num_destinations)


def test_expected_units_match_the_stream() -> None:
    from crossdock_solver.stream.demand import StationaryDemand

    env = _c3_env(measure_to=2000)
    while not env.done:
        env.dispatch(*FCFSRulePolicy().act(env))
    trucks = [t for t in env.departed if t.uid >= 0]
    horizon = max(t.arrival for t in trucks)
    observed = np.sum([t.units for t in trucks], axis=0)
    expected = StationaryDemand(env.facility).expected_units(0.0, horizon)
    assert np.allclose(observed, expected, rtol=0.1)


def test_claim_now_policy_reproduces_model_without_claim_decision() -> None:
    a = run_stream(_c3_env(), FCFSRulePolicy())
    b = run_stream(_c3_env(max_extensions=2), FCFSRulePolicy())
    assert a.objective == b.objective


def test_extension_takes_freight_unloaded_meanwhile() -> None:
    env = _c3_env(max_extensions=1)
    metrics = run_stream(env, _AlwaysExtend())
    carriers = [t for t in env.departed if t.uid >= 0]
    assert all(t.extensions == 1 for t in carriers)
    wait = env.config.extension_work * env.facility.mean_work
    for truck in carriers:
        # claimed one extension after its first claim moment
        first = truck.dock_time + truck.enter + (
            float(truck.handling.sum() - truck.handling[truck.destination]) if truck.compound else 0.0)
        assert truck.claim_time == pytest.approx(first + wait)
        assert all(lot.source.dock_time <= truck.claim_time for lot in truck.lots)
    assert metrics.objective != run_stream(_c3_env(), FCFSRulePolicy()).objective


def test_fork_at_pending_claim_and_rollout_claim_decision() -> None:
    from crossdock_solver.stream.demand import demand_model
    from crossdock_solver.stream.rollout import RolloutPolicy

    env = _c3_env(amplitude=0.6, dest_amplitude=0.6, max_extensions=2, measure_to=60)
    while not env.needs_claim:
        env.dispatch(*FCFSRulePolicy().act(env))
    pending = env.pending_claim
    sim = env.fork(seed=0, until=env.now + env.facility.sla)
    assert sim.pending_claim is not pending and sim.pending_claim.uid == pending.uid
    sim.resolve_claim(True)
    assert env.pending_claim is pending and pending.extensions == 0
    for level in ("I0", "I1", "I2"):
        policy = RolloutPolicy(samples=2, horizon_sla=0.3, demand=demand_model(level, env.facility, seed=1))
        assert isinstance(policy.claim(env, pending), bool)
    metrics = run_stream(_c3_env(amplitude=0.6, dest_amplitude=0.6, max_extensions=2, measure_to=60),
                         RolloutPolicy(samples=2, horizon_sla=0.3))
    assert metrics.trucks == 40
