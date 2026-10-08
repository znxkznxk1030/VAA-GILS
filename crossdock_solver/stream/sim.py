"""Discrete-event simulator of a cross-dock with an endless truck stream.

Process (compound-truck mechanics of the static model, generalized):

- Trucks arrive (Poisson) and wait in the yard. A compound truck carries
  freight for every destination; an outbound truck arrives empty.
- Whenever a door is free and the yard is not empty, the policy either
  dispatches one yard truck to one free door with a destination, or holds.
- A compound truck retaining destination d enters, partially unloads all
  freight for the other destinations (it becomes a staged lot at its door,
  ready when unloading ends), then acts as the carrier of d. An outbound
  truck for d enters and acts as the carrier of d.
- Claim rule: when a carrier starts its loading phase it takes every
  unclaimed lot for d of compound trucks already docked, waits until each lot
  is unloaded and moved to its door (travel time), loads it, and leaves.
  Lots unloaded later wait for the next carrier of d.

Objective (long-run average, trucks of the measurement window):
    J = mean freight lead time (per unit: carrier departure - compound arrival)
        + lambda * mean truck tardiness (due = arrival + SLA).
The simulator also accrues the same cost continuously so a learning agent can
receive it as a dense reward between decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import itertools
import math

import numpy as np

from crossdock_solver.stream.config import Facility, StreamConfig, build_facility


ARRIVE, CLAIM, DEPART = 0, 1, 2


@dataclass(eq=False)
class Truck:
    uid: int
    compound: bool
    arrival: float
    due: float
    enter: float
    leave: float
    units: np.ndarray  # units per destination (zeros for outbound trucks)
    handling: np.ndarray  # handling time per destination
    door: int = -1
    destination: int = -1
    dock_time: float = math.nan
    claim_time: float = math.nan
    departure: float = math.nan
    lots: list["Lot"] = field(default_factory=list)

    @property
    def retained_units(self) -> float:
        return float(self.units[self.destination]) if self.compound else 0.0

    @property
    def carried_units(self) -> float:
        return self.retained_units + sum(lot.units for lot in self.lots)


@dataclass(eq=False)
class Lot:
    source: Truck
    destination: int
    units: float
    handling: float
    door: int
    ready: float


@dataclass
class StreamMetrics:
    trucks: int
    mean_lead: float
    mean_tardiness: float
    mean_sojourn: float
    mean_yard_wait: float
    objective: float
    empty_outbound_rate: float
    undelivered_units: float
    utilization: float

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class CrossDockStream:
    """Event-driven environment. Call `reset`, then alternate `dispatch`/`hold`
    while `needs_decision`; `done` turns true once every truck of the
    measurement window has departed and its freight has been carried."""

    def __init__(
        self,
        config: StreamConfig,
        seed: int,
        *,
        measure_from: int = 100,
        measure_to: int = 600,
        max_candidates: int = 6,
        time_cap_factor: float = 20.0,
    ) -> None:
        self.config = config
        self.seed = seed
        self.measure_from = measure_from
        self.measure_to = measure_to
        self.max_candidates = max_candidates
        self.time_cap_factor = time_cap_factor
        self.reset()

    # ------------------------------------------------------------------ setup
    def reset(self) -> None:
        self.facility: Facility = build_facility(self.config, np.random.default_rng(self.seed))
        self._rng = np.random.default_rng(self.seed + 1)
        self.now = 0.0
        self.yard: list[Truck] = []
        self.doors: list[Truck | None] = [None] * self.config.num_doors
        self.open_lots: list[list[Lot]] = [[] for _ in range(self.config.num_destinations)]
        self.in_system: list[Truck] = []
        self.departed: list[Truck] = []
        self.units_in_system = 0.0
        self.unit_integral = 0.0
        self.tardy_integral = 0.0
        self.busy_integral = 0.0
        self.last_departure = np.full(self.config.num_destinations, 0.0)
        self._events: list[tuple[float, int, int, Truck | None]] = []
        self._seq = itertools.count()
        self._uid = itertools.count()
        self._held = False
        self._arrivals = 0
        self._measured: list[Truck] = []
        self._time_cap = math.inf
        self.done = False
        self._schedule(self._interarrival(), ARRIVE, None)
        self._advance()

    # -------------------------------------------------------------- decisions
    @property
    def needs_decision(self) -> bool:
        return not self.done and not self._held and bool(self.yard) and any(
            truck is None for truck in self.doors
        )

    def free_doors(self) -> list[int]:
        return [m for m, truck in enumerate(self.doors) if truck is None]

    def candidates(self) -> list[tuple[Truck, int, int]]:
        trucks = self.yard[: self.max_candidates]
        doors = self.free_doors()
        destinations = range(self.config.num_destinations)
        return [(t, m, d) for t in trucks for m in doors for d in destinations]

    def dispatch(self, truck: Truck, door: int, destination: int) -> None:
        if not self.needs_decision:
            raise RuntimeError("no decision pending")
        if truck not in self.yard:
            raise ValueError("truck is not waiting in the yard")
        if self.doors[door] is not None:
            raise ValueError(f"door {door} is busy")
        if not 0 <= destination < self.config.num_destinations:
            raise ValueError(f"unknown destination {destination}")
        self.yard.remove(truck)
        self.doors[door] = truck
        truck.door = door
        truck.destination = destination
        truck.dock_time = self.now
        if truck.compound:
            unload = float(truck.handling.sum() - truck.handling[destination])
            ready = self.now + truck.enter + unload
            for d in range(self.config.num_destinations):
                if d != destination and truck.units[d] > 0:
                    self.open_lots[d].append(
                        Lot(truck, d, float(truck.units[d]), float(truck.handling[d]), door, ready)
                    )
            self._schedule(ready, CLAIM, truck)
        else:
            self._schedule(self.now + truck.enter, CLAIM, truck)
        self._advance()

    def hold(self) -> None:
        if not self.needs_decision:
            raise RuntimeError("no decision pending")
        self._held = True
        self._advance()

    # ----------------------------------------------------------------- reward
    def cost_snapshot(self) -> float:
        """Accrued cost so far in J units x trucks: unit-time / mean units
        plus lambda * truck tardiness time."""

        return (
            self.unit_integral / self.facility.mean_units
            + self.config.tardiness_weight * self.tardy_integral
        )

    # ---------------------------------------------------------------- engine
    def _schedule(self, time: float, kind: int, truck: Truck | None) -> None:
        heapq.heappush(self._events, (time, next(self._seq), kind, truck))

    def _interarrival(self) -> float:
        return float(self._rng.exponential(1.0 / self.facility.arrival_rate))

    def _advance(self) -> None:
        while not self.done and not self.needs_decision:
            if not self._events:
                self.done = True
                break
            time, _, kind, truck = heapq.heappop(self._events)
            if time > self._time_cap:
                self._accrue(self._time_cap)
                self.done = True
                break
            self._accrue(time)
            if kind == ARRIVE:
                self._on_arrive()
            elif kind == CLAIM:
                self._on_claim(truck)
            else:
                self._on_depart(truck)
            if self._finished():
                self.done = True

    def _accrue(self, time: float) -> None:
        dt = time - self.now
        if dt > 0:
            self.unit_integral += self.units_in_system * dt
            for truck in self.in_system:
                if time > truck.due:
                    self.tardy_integral += time - max(self.now, truck.due)
            self.busy_integral += dt * sum(truck is not None for truck in self.doors)
            self.now = time

    def _on_arrive(self) -> None:
        cfg = self.config
        fac = self.facility
        rng = self._rng
        compound = bool(rng.random() < cfg.compound_fraction)
        if compound:
            highs = np.floor(cfg.flow_high * fac.demand_weight).astype(int) + 1
            cargo = rng.integers(0, highs[:, None], size=(cfg.num_destinations, cfg.num_products))
            units = cargo.sum(axis=1).astype(float)
            handling = (cargo @ fac.product_time).astype(float)
        else:
            units = np.zeros(cfg.num_destinations)
            handling = np.zeros(cfg.num_destinations)
        truck = Truck(
            uid=next(self._uid),
            compound=compound,
            arrival=self.now,
            due=self.now + fac.sla,
            enter=float(rng.integers(1, 6)),
            leave=float(rng.integers(1, 6)),
            units=units,
            handling=handling,
        )
        self.yard.append(truck)
        self.in_system.append(truck)
        self.units_in_system += float(units.sum())
        if self.measure_from <= truck.uid < self.measure_to:
            self._measured.append(truck)
        self._arrivals += 1
        if self._arrivals == self.measure_to:
            self._time_cap = self.now + self.time_cap_factor * fac.sla
        self._held = False
        self._schedule(self.now + self._interarrival(), ARRIVE, None)

    def _on_claim(self, truck: Truck) -> None:
        d = truck.destination
        lots = self.open_lots[d]
        self.open_lots[d] = []
        truck.claim_time = self.now
        truck.lots = lots
        travel = self.facility.travel
        start = self.now
        load = 0.0
        for lot in lots:
            start = max(start, lot.ready + travel[lot.door, truck.door])
            load += lot.handling
        self._schedule(start + load + truck.leave, DEPART, truck)

    def _on_depart(self, truck: Truck) -> None:
        truck.departure = self.now
        self.doors[truck.door] = None
        self.in_system.remove(truck)
        self.departed.append(truck)
        self.units_in_system -= truck.carried_units
        self.last_departure[truck.destination] = self.now
        self._held = False

    def _finished(self) -> bool:
        if self._arrivals < self.measure_to:
            return False
        for truck in self._measured:
            if math.isnan(truck.departure):
                return False
        return self._measured_freight_delivered()

    def _measured_freight_delivered(self) -> bool:
        lo, hi = self.measure_from, self.measure_to
        for lots in self.open_lots:
            if any(lo <= lot.source.uid < hi for lot in lots):
                return False
        for truck in self.in_system:
            if any(lo <= lot.source.uid < hi for lot in truck.lots):
                return False
        return True

    # --------------------------------------------------------------- metrics
    def metrics(self) -> StreamMetrics:
        measured = self._measured
        lo, hi = self.measure_from, self.measure_to
        end = self.now
        lead_sum = 0.0
        units_sum = 0.0
        undelivered = 0.0
        for truck in self.departed:
            for lot in truck.lots:
                if lo <= lot.source.uid < hi:
                    lead_sum += lot.units * (truck.departure - lot.source.arrival)
                    units_sum += lot.units
            if truck.compound and lo <= truck.uid < hi:
                lead_sum += truck.retained_units * (truck.departure - truck.arrival)
                units_sum += truck.retained_units
        # Censor freight still in the dock at the end (only under a time cap).
        for lots in self.open_lots:
            for lot in lots:
                if lo <= lot.source.uid < hi:
                    lead_sum += lot.units * (end - lot.source.arrival)
                    units_sum += lot.units
                    undelivered += lot.units
        for truck in self.in_system:
            carried = [lot for lot in truck.lots if lo <= lot.source.uid < hi]
            for lot in carried:
                lead_sum += lot.units * (end - lot.source.arrival)
                units_sum += lot.units
                undelivered += lot.units

        finish = [t.departure if not math.isnan(t.departure) else end for t in measured]
        tardiness = [max(0.0, f - t.due) for f, t in zip(finish, measured)]
        sojourn = [f - t.arrival for f, t in zip(finish, measured)]
        dock = [t.dock_time if not math.isnan(t.dock_time) else end for t in measured]
        yard_wait = [dk - t.arrival for dk, t in zip(dock, measured)]
        outbound = [t for t in measured if not t.compound and not math.isnan(t.departure)]
        empty = sum(1 for t in outbound if not t.lots)
        mean_lead = lead_sum / units_sum if units_sum else 0.0
        mean_tard = float(np.mean(tardiness)) if tardiness else 0.0
        return StreamMetrics(
            trucks=len(measured),
            mean_lead=mean_lead,
            mean_tardiness=mean_tard,
            mean_sojourn=float(np.mean(sojourn)) if sojourn else 0.0,
            mean_yard_wait=float(np.mean(yard_wait)) if yard_wait else 0.0,
            objective=mean_lead + self.config.tardiness_weight * mean_tard,
            empty_outbound_rate=empty / len(outbound) if outbound else 0.0,
            undelivered_units=undelivered,
            utilization=self.busy_integral / (self.config.num_doors * self.now) if self.now else 0.0,
        )


def run_stream(env: CrossDockStream, policy) -> StreamMetrics:
    """Drive `env` with `policy.act(env) -> (truck, door, destination) | None`."""

    if hasattr(policy, "reset"):
        policy.reset(env)
    while not env.done:
        action = policy.act(env)
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)
    return env.metrics()
