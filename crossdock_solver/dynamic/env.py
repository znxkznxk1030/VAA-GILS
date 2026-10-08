"""Event-driven environment for the dynamic compound-truck cross-dock.

Decision epochs are truck arrivals in realized order. At each epoch the
policy sees a `DockView`: the static data, the arrival-noise model, the
current time, the arrivals revealed so far and the decisions already
committed. It never sees future arrivals. After the last decision the
committed assignment is evaluated on the realized instance.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np

from crossdock_solver.core.evaluator import ScheduleResult, evaluate_solution
from crossdock_solver.core.solution import Solution
from crossdock_solver.data.instance import CrossDockInstance, DestinationId, DoorId, TruckId
from crossdock_solver.dynamic.plan import Decision, forecast_instance, tardiness_weight
from crossdock_solver.dynamic.scenario import ArrivalNoise, DynamicScenario


Action = tuple[DestinationId, DoorId]


@dataclass(frozen=True)
class DockView:
    """Information available to a policy at one decision epoch."""

    planned: CrossDockInstance
    noise: ArrivalNoise
    horizon: float
    time: float
    truck: TruckId
    step: int
    arrived: Mapping[TruckId, float]
    commitments: tuple[Decision, ...]
    manifests: Mapping[TruckId, np.ndarray] = MappingProxyType({})

    @property
    def is_compound(self) -> bool:
        return self.truck in self.planned.compound_index

    @property
    def weight(self) -> float:
        return tardiness_weight(self.planned)

    def free_destinations(self) -> list[DestinationId]:
        taken = {decision.destination for decision in self.commitments}
        return [d for d in self.planned.destinations if d not in taken]

    def legal_doors(self) -> list[DoorId]:
        if not self.is_compound:
            return list(self.planned.doors)
        taken = {
            decision.door
            for decision in self.commitments
            if decision.truck in self.planned.compound_index
        }
        return [m for m in self.planned.doors if m not in taken]

    def legal_actions(self) -> list[Action]:
        doors = self.legal_doors()
        return [(d, m) for d in self.free_destinations() for m in doors]

    def forecast(self) -> CrossDockInstance:
        return forecast_instance(self.planned, self.time, self.arrived, self.manifests)


class DynamicDockEnv:
    def __init__(self, scenario: DynamicScenario) -> None:
        self.scenario = scenario
        self._order = scenario.arrival_order()
        self.reset()

    def reset(self) -> DockView:
        self._step = 0
        self._commitments: list[Decision] = []
        return self.view()

    @property
    def done(self) -> bool:
        return self._step >= len(self._order)

    @property
    def commitments(self) -> tuple[Decision, ...]:
        return tuple(self._commitments)

    def view(self) -> DockView:
        if self.done:
            raise RuntimeError("episode finished; no pending decision")
        truck = self._order[self._step]
        now = self.scenario.arrival[truck]
        arrived = {
            t: r for t, r in self.scenario.arrival.items() if r <= now
        }
        manifests = {}
        if self.scenario.flow is not None:
            planned = self.scenario.planned
            manifests = {
                t: self.scenario.flow[planned.compound_index[t]].copy()
                for t in arrived
                if t in planned.compound_index
            }
        return DockView(
            planned=self.scenario.planned,
            noise=self.scenario.noise,
            horizon=self.scenario.horizon,
            time=now,
            truck=truck,
            step=self._step,
            arrived=MappingProxyType(arrived),
            commitments=tuple(self._commitments),
            manifests=MappingProxyType(manifests),
        )

    def step(self, destination: DestinationId, door: DoorId) -> DockView | None:
        view = self.view()
        if destination not in view.free_destinations():
            raise ValueError(f"destination {destination} is not free for {view.truck}")
        if door not in view.legal_doors():
            raise ValueError(f"door {door} is not legal for {view.truck}")
        self._commitments.append(Decision(view.truck, destination, door))
        self._step += 1
        return None if self.done else self.view()

    def solution(self) -> Solution:
        if not self.done:
            raise RuntimeError("episode not finished")
        planned = self.scenario.planned
        solution = Solution(
            compound_assignment={},
            outbound_assignment={},
            door_sequences={door: [] for door in planned.doors},
        )
        for decision in self._commitments:
            assignment = (decision.destination, decision.door)
            if decision.truck in planned.compound_index:
                solution.compound_assignment[decision.truck] = assignment
            else:
                solution.outbound_assignment[decision.truck] = assignment
                solution.door_sequences[decision.door].append(decision.truck)
        return solution

    def result(self) -> ScheduleResult:
        return evaluate_solution(self.scenario.realized_instance(), self.solution())
