"""Non-learning reference policies and the episode runner.

Hierarchy (each adds one capability to the previous one):

- `RandomPolicy`: uniform over legal actions (floor).
- `StaticPlanPolicy`: one GILS plan at time 0 on planned arrivals, followed
  as closely as commitments allow (no re-planning).
- `GreedyRepairPolicy`: same plan, but every arrival tries all legal actions,
  completes the rest by projecting the current plan and keeps the action whose
  completed plan scores best on the certainty-equivalent forecast.
- `RollingGILSPolicy`: certainty-equivalent re-optimization; GILS re-plans the
  uncommitted part at every arrival, warm-started from the previous plan.

`hindsight` solves the realized instance with full information; it is the
clairvoyant reference against which online policies are measured.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Protocol, Sequence

from crossdock_solver.baselines.vaa_qrl import ACTIONS_TW, VaaQRLConfig, run_vaa_qrl
from crossdock_solver.core.evaluator import evaluate_solution
from crossdock_solver.core.fast_evaluator import FastEvaluator
from crossdock_solver.core.solution import Solution
from crossdock_solver.data.instance import CrossDockInstance
from crossdock_solver.dynamic.env import Action, DockView, DynamicDockEnv
from crossdock_solver.dynamic.plan import (
    Decision,
    assignment_of,
    project,
    tardiness_weight,
)
from crossdock_solver.dynamic.scenario import DynamicScenario
from crossdock_solver.rl.selectors import UniformSelector


class Policy(Protocol):
    name: str

    def reset(self, view: DockView) -> None: ...

    def decide(self, view: DockView) -> Action: ...


def gils_plan(
    instance: CrossDockInstance,
    *,
    iterations: int,
    seed: int,
    initial: Solution | None = None,
    commitments: Sequence[Decision] = (),
) -> Solution:
    """Final paper engine (uniform selection, greedy acceptance) with commitments fixed."""

    commitments = tuple(commitments)
    project_fn = (lambda s: project(instance, s, commitments)) if commitments else None
    run = run_vaa_qrl(
        instance,
        VaaQRLConfig(
            max_iterations=iterations,
            tardiness_weight=tardiness_weight(instance),
            seed=seed,
            use_sa_acceptance=False,
        ),
        initial_solution=initial,
        selector=UniformSelector(ACTIONS_TW),
        project=project_fn,
    )
    return run.solution


class RandomPolicy:
    name = "Random"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def reset(self, view: DockView) -> None:
        self._rng = random.Random(self.seed)

    def decide(self, view: DockView) -> Action:
        return self._rng.choice(view.legal_actions())


class StaticPlanPolicy:
    name = "StaticPlan"

    def __init__(self, iterations: int = 1000, seed: int = 0) -> None:
        self.iterations = iterations
        self.seed = seed

    def reset(self, view: DockView) -> None:
        self.plan = gils_plan(view.forecast(), iterations=self.iterations, seed=self.seed)

    def decide(self, view: DockView) -> Action:
        self.plan = project(view.planned, self.plan, view.commitments)
        return assignment_of(self.plan, view.truck)


class GreedyRepairPolicy(StaticPlanPolicy):
    name = "Greedy"

    def decide(self, view: DockView) -> Action:
        forecast = view.forecast()
        fast = FastEvaluator(forecast, tardiness_weight=view.weight)
        best_plan: Solution | None = None
        best_action: Action | None = None
        best_score = float("inf")
        for destination, door in view.legal_actions():
            candidate = project(
                forecast,
                self.plan,
                (*view.commitments, Decision(view.truck, destination, door)),
            )
            score = fast.evaluate(candidate).objective
            if score < best_score:
                best_plan, best_action, best_score = candidate, (destination, door), score
        assert best_plan is not None and best_action is not None
        self.plan = best_plan
        return best_action


class RollingGILSPolicy(StaticPlanPolicy):
    name = "Rolling-GILS"

    def __init__(
        self,
        iterations: int = 200,
        initial_iterations: int = 1000,
        seed: int = 0,
    ) -> None:
        super().__init__(iterations=initial_iterations, seed=seed)
        self.replan_iterations = iterations

    def decide(self, view: DockView) -> Action:
        self.plan = gils_plan(
            view.forecast(),
            iterations=self.replan_iterations,
            seed=self.seed * 1_000 + view.step + 1,
            initial=self.plan,
            commitments=view.commitments,
        )
        return assignment_of(self.plan, view.truck)


@dataclass
class EpisodeResult:
    policy: str
    objective: float
    makespan: float
    total_tardiness: float
    plan_sec: float
    decide_sec_total: float
    decide_sec_max: float
    solution: Solution


def run_episode(scenario: DynamicScenario, policy: Policy) -> EpisodeResult:
    env = DynamicDockEnv(scenario)
    view = env.reset()
    start = time.perf_counter()
    policy.reset(view)
    plan_sec = time.perf_counter() - start

    decide_total = 0.0
    decide_max = 0.0
    while view is not None:
        start = time.perf_counter()
        destination, door = policy.decide(view)
        elapsed = time.perf_counter() - start
        decide_total += elapsed
        decide_max = max(decide_max, elapsed)
        view = env.step(destination, door)

    result = env.result()
    weight = tardiness_weight(scenario.planned)
    return EpisodeResult(
        policy=policy.name,
        objective=result.makespan + weight * result.total_tardiness,
        makespan=result.makespan,
        total_tardiness=result.total_tardiness,
        plan_sec=plan_sec,
        decide_sec_total=decide_total,
        decide_sec_max=decide_max,
        solution=env.solution(),
    )


def hindsight(scenario: DynamicScenario, *, iterations: int = 1000, seed: int = 0) -> EpisodeResult:
    realized = scenario.realized_instance()
    start = time.perf_counter()
    solution = gils_plan(realized, iterations=iterations, seed=seed)
    elapsed = time.perf_counter() - start
    result = evaluate_solution(realized, solution)
    return EpisodeResult(
        policy="Hindsight",
        objective=result.makespan + tardiness_weight(realized) * result.total_tardiness,
        makespan=result.makespan,
        total_tardiness=result.total_tardiness,
        plan_sec=elapsed,
        decide_sec_total=0.0,
        decide_sec_max=0.0,
        solution=solution,
    )
