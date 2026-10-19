"""Finite truck sets for the hindsight benchmark.

A finite instance is the first `n` trucks of a stream (same arrival process and
cargo sampler as `CrossDockStream`). Freight that no truck of the instance
carries is taken by a terminal sweeper: once every truck has left (time Cmax),
one virtual carrier per destination with stranded lots loads them (no travel)
and leaves after `SWEEP_LEAVE`; sweepers are not trucks of the instance (no
tardiness) and the CP-SAT model applies the same rule. All
times are on a 0.01 grid (arrivals are rounded, travel times already are,
entry/exit and handling times are integers), so the simulator and the CP-SAT
model of `hindsight.py` evaluate a schedule identically.

`FiniteStream` replays such an instance in the simulator: every truck is
measured, the system starts empty, and the run ends when every truck has left
and all freight is delivered. Online policies know the shift length (n trucks)
but not when the trucks arrive or what they carry: look-ahead forks are plain
`CrossDockStream`s that resample a Poisson future of at most n trucks in total
(`max_arrivals`) and apply the same sweeper. Due dates are rounded to the grid
as well. A hold with nothing left to happen (no pending event) would end the
run with trucks in the yard, so it is replaced by the FCFS-VAA action.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from crossdock_solver.stream.config import Facility, StreamConfig, build_facility
from crossdock_solver.stream.sim import SWEEP_LEAVE, CrossDockStream, Truck  # noqa: F401 (re-export)


@dataclass(frozen=True)
class TruckSpec:
    compound: bool
    arrival: float
    enter: float
    leave: float
    units: tuple[float, ...]
    handling: tuple[float, ...]


@dataclass(frozen=True)
class FiniteInstance:
    config: StreamConfig
    seed: int
    trucks: tuple[TruckSpec, ...]

    @property
    def facility(self) -> Facility:
        return build_facility(self.config, np.random.default_rng(self.seed))


def sample_finite_instance(config: StreamConfig, seed: int, n: int, *, closers: bool = False) -> FiniteInstance:
    """First `n` stream trucks (+ optionally |D| outbound trucks right after the last)."""

    fac = build_facility(config, np.random.default_rng(seed))
    rng = np.random.default_rng(seed + 1)
    D = config.num_destinations
    highs = np.floor(config.flow_high * fac.demand_weight).astype(int) + 1
    trucks: list[TruckSpec] = []
    now = 0.0
    for _ in range(n):
        now = round(now + float(rng.exponential(1.0 / fac.arrival_rate)), 2)
        compound = bool(rng.random() < config.compound_fraction)
        if compound:
            cargo = rng.integers(0, highs[:, None], size=(D, config.num_products))
            units = cargo.sum(axis=1).astype(float)
            handling = (cargo @ fac.product_time).astype(float)
        else:
            units = handling = np.zeros(D)
        trucks.append(TruckSpec(compound, now, float(rng.integers(1, 6)), float(rng.integers(1, 6)),
                                tuple(units.tolist()), tuple(handling.tolist())))
    if closers:
        for k in range(D):
            trucks.append(TruckSpec(False, round(now + 0.01 * (k + 1), 2), float(rng.integers(1, 6)),
                                    float(rng.integers(1, 6)), (0.0,) * D, (0.0,) * D))
    return FiniteInstance(config, seed, tuple(trucks))


class FiniteStream(CrossDockStream):
    """Simulator replaying a `FiniteInstance` (all trucks measured)."""

    def __init__(self, instance: FiniteInstance, *, max_candidates: int = 6) -> None:
        self.instance = instance
        n = len(instance.trucks)
        super().__init__(instance.config, instance.seed, measure_from=0, measure_to=n,
                         max_candidates=max_candidates, time_cap_factor=math.inf, max_arrivals=n)

    def reset(self) -> None:
        self._next = 0
        super().reset()

    def _interarrival(self) -> float:
        specs = self.instance.trucks
        if self._next >= len(specs):
            return math.inf
        return specs[self._next].arrival - self.now

    def _schedule(self, time: float, kind: int, truck) -> None:
        if math.isfinite(time):
            super()._schedule(time, kind, truck)

    def _on_arrive(self) -> None:
        spec = self.instance.trucks[self._next]
        self._next += 1
        self.now = spec.arrival  # exact grid value (no float drift from now + dt)
        truck = Truck(
            uid=next(self._uid),
            compound=spec.compound,
            arrival=spec.arrival,
            due=round(spec.arrival + self.facility.sla, 2),
            enter=spec.enter,
            leave=spec.leave,
            units=np.array(spec.units),
            handling=np.array(spec.handling),
        )
        self.yard.append(truck)
        self.in_system.append(truck)
        self.units_in_system += float(truck.units.sum())
        self._measured.append(truck)
        self._arrivals += 1
        self._held = False
        self._schedule(self.now + self._interarrival(), 0, None)
