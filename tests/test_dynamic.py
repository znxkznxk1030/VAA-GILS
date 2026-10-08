from __future__ import annotations

import random

import pytest

from crossdock_solver.baselines.vaa import vaa_solution
from crossdock_solver.core.evaluator import evaluate_solution
from crossdock_solver.core.feasibility import check_feasible
from crossdock_solver.data.generator import generate_benchmark_instance
from crossdock_solver.dynamic.env import DynamicDockEnv
from crossdock_solver.dynamic.plan import Decision, assignment_of, project
from crossdock_solver.dynamic.policies import (
    GreedyRepairPolicy,
    RandomPolicy,
    RollingGILSPolicy,
    StaticPlanPolicy,
    gils_plan,
    hindsight,
    run_episode,
)
from crossdock_solver.dynamic.scenario import ArrivalNoise, make_scenario


def _planned(tw: str | None = "medium", seed: int = 7):
    return generate_benchmark_instance("S", seed=seed, tw_tightness=tw)


def _random_commitments(scenario, seed: int, count: int) -> list[Decision]:
    rng = random.Random(seed)
    env = DynamicDockEnv(scenario)
    view = env.reset()
    for _ in range(count):
        destination, door = rng.choice(view.legal_actions())
        view = env.step(destination, door)
    return list(env.commitments)


def test_scenario_is_deterministic_and_non_negative() -> None:
    planned = _planned()
    first = make_scenario(planned, "high", seed=3)
    second = make_scenario(planned, "high", seed=3)
    other = make_scenario(planned, "high", seed=4)
    assert first.arrival == second.arrival
    assert first.arrival != other.arrival
    assert all(r >= 0 for r in first.arrival.values())
    assert first.planned.due_time == planned.due_time


def test_zero_noise_reproduces_planned_arrivals() -> None:
    planned = _planned()
    scenario = make_scenario(planned, ArrivalNoise(0.0, 0.0, 0.0), seed=1)
    assert scenario.arrival == {t: round(r, 1) for t, r in planned.release_time.items()}


def test_conditional_sample_is_after_the_condition() -> None:
    noise = ArrivalNoise(0.05, 0.2, 0.1)
    rng = random.Random(0)
    for after in (0.0, 50.0, 500.0, 5000.0):
        assert all(noise.sample_after(rng, 10.0, 200.0, after) > after for _ in range(50))


@pytest.mark.parametrize("seed", range(5))
def test_project_honours_commitments(seed: int) -> None:
    scenario = make_scenario(_planned(), "medium", seed=seed)
    instance = scenario.planned
    base = vaa_solution(instance)
    commitments = _random_commitments(scenario, seed, count=6)

    plan = project(instance, base, commitments)

    check_feasible(instance, plan)
    for decision in commitments:
        assert assignment_of(plan, decision.truck) == (decision.destination, decision.door)
    for door, sequence in plan.door_sequences.items():
        committed_here = [d.truck for d in commitments if d.door == door and d.truck in instance.outbound_trucks]
        assert sequence[: len(committed_here)] == committed_here


def test_project_without_commitments_is_identity() -> None:
    instance = _planned()
    base = vaa_solution(instance)
    plan = project(instance, base, [])
    assert plan.compound_assignment == base.compound_assignment
    assert plan.outbound_assignment == base.outbound_assignment
    assert plan.door_sequences == base.door_sequences


def test_view_never_reveals_future_arrivals() -> None:
    scenario = make_scenario(_planned(), "high", seed=11)
    env = DynamicDockEnv(scenario)
    view = env.reset()
    rng = random.Random(0)
    while view is not None:
        assert all(r <= view.time for r in view.arrived.values())
        assert view.truck in view.arrived
        future = {t for t, r in scenario.arrival.items() if r > view.time}
        assert future.isdisjoint(view.arrived)
        view = env.step(*rng.choice(view.legal_actions()))


def test_illegal_actions_are_rejected() -> None:
    scenario = make_scenario(_planned(), "low", seed=2)
    env = DynamicDockEnv(scenario)
    view = env.reset()
    destination, door = view.legal_actions()[0]
    env.step(destination, door)
    view = env.view()
    with pytest.raises(ValueError):
        env.step(destination, view.legal_doors()[0])


def test_final_solution_is_evaluated_on_realized_arrivals() -> None:
    scenario = make_scenario(_planned(), "medium", seed=5)
    result = run_episode(scenario, RandomPolicy(seed=0))
    realized = scenario.realized_instance()
    check_feasible(realized, result.solution)
    reference = evaluate_solution(realized, result.solution)
    assert result.makespan == pytest.approx(reference.makespan)
    assert result.total_tardiness == pytest.approx(reference.total_tardiness)
    for truck, start in reference.truck_start.items():
        assert start >= scenario.arrival[truck] - 1e-9


def test_gils_plan_keeps_commitments_fixed() -> None:
    scenario = make_scenario(_planned(), "medium", seed=8)
    commitments = _random_commitments(scenario, 8, count=5)
    plan = gils_plan(scenario.planned, iterations=60, seed=0, commitments=commitments)
    check_feasible(scenario.planned, plan)
    for decision in commitments:
        assert assignment_of(plan, decision.truck) == (decision.destination, decision.door)


@pytest.mark.parametrize(
    "policy",
    [
        RandomPolicy(seed=0),
        StaticPlanPolicy(iterations=50),
        GreedyRepairPolicy(iterations=50),
        RollingGILSPolicy(iterations=20, initial_iterations=50),
    ],
    ids=lambda p: p.name,
)
def test_policies_complete_an_episode(policy) -> None:
    scenario = make_scenario(_planned(), "medium", seed=9)
    result = run_episode(scenario, policy)
    check_feasible(scenario.realized_instance(), result.solution)
    assert result.objective > 0


def test_static_plan_follows_plan_without_noise() -> None:
    scenario = make_scenario(_planned(), ArrivalNoise(0.0, 0.0, 0.0), seed=0)
    policy = StaticPlanPolicy(iterations=50)
    result = run_episode(scenario, policy)
    plan = gils_plan(scenario.planned, iterations=50, seed=0)
    assert result.solution.compound_assignment == plan.compound_assignment
    assert result.solution.outbound_assignment == plan.outbound_assignment


def test_hindsight_is_not_worse_than_random() -> None:
    scenario = make_scenario(_planned(), "medium", seed=10)
    clairvoyant = hindsight(scenario, iterations=100)
    online = run_episode(scenario, RandomPolicy(seed=0))
    assert clairvoyant.objective <= online.objective + 1e-6


def test_manifests_are_revealed_only_on_arrival() -> None:
    planned = _planned()
    scenario = make_scenario(planned, "medium", seed=12, manifest="high")
    assert scenario.flow is not None and not (scenario.flow == planned.flow).all()
    env = DynamicDockEnv(scenario)
    view = env.reset()
    rng = random.Random(1)
    while view is not None:
        assert set(view.manifests) == {t for t in view.arrived if t in planned.compound_index}
        forecast = view.forecast()
        for truck in planned.compound_trucks:
            row = forecast.flow[planned.compound_index[truck]]
            expected = scenario.flow if truck in view.arrived else planned.flow
            assert (row == expected[planned.compound_index[truck]]).all()
        view = env.step(*rng.choice(view.legal_actions()))
    assert (env.result().makespan == evaluate_solution(scenario.realized_instance(), env.solution()).makespan)
