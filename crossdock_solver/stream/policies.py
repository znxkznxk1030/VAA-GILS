"""Reference policies for the continuous cross-dock.

- `FCFSRulePolicy`: work-conserving dispatching. The earliest yard truck goes to
  a free door. A compound truck retains the destination with the most own
  handling (the per-truck essence of the VAA regret rule) or, with
  `backlog=True`, own handling plus the waiting backlog; an outbound truck
  serves the destination with the largest claimable backlog.
- `CyclicPlanPolicy`: the static method applied as-is. Its model needs exactly
  one carrier per destination, so arriving trucks are grouped first-come
  first-served into cycles of |D| trucks (|I_c| + |F_c| = |D|), each cycle is
  solved as a static instance by VAA or VAA-GILS, and the plan is executed door
  by door (compound first, then the outbound sequence).
"""

from __future__ import annotations

import time

import numpy as np

from crossdock_solver.baselines.vaa import vaa_solution
from crossdock_solver.baselines.vaa_qrl import ACTIONS_TW, VaaQRLConfig, run_vaa_qrl
from crossdock_solver.data.instance import CrossDockInstance
from crossdock_solver.rl.selectors import UniformSelector
from crossdock_solver.stream.sim import CrossDockStream, Truck


def backlog_handling(env: CrossDockStream) -> np.ndarray:
    """Handling time of unclaimed lots per destination (docked compound trucks)."""

    out = np.zeros(env.config.num_destinations)
    for d, lots in enumerate(env.open_lots):
        out[d] = sum(lot.handling for lot in lots)
    return out


def central_door(env: CrossDockStream, doors: list[int]) -> int:
    travel = env.facility.travel
    return min(doors, key=lambda m: (travel[m].mean(), m))


def nearest_door_to_lots(env: CrossDockStream, doors: list[int], destination: int) -> int:
    lots = env.open_lots[destination]
    if not lots:
        return central_door(env, doors)
    travel = env.facility.travel
    return min(
        doors,
        key=lambda m: (sum(lot.units * travel[lot.door, m] for lot in lots), m),
    )


class FCFSRulePolicy:
    def __init__(self, *, backlog: bool = False) -> None:
        self.backlog = backlog
        self.name = "FCFS-Backlog" if backlog else "FCFS-VAA"

    def act(self, env: CrossDockStream):
        truck = env.yard[0]
        doors = env.free_doors()
        waiting = backlog_handling(env)
        if truck.compound:
            score = truck.handling + (waiting if self.backlog else 0.0)
            destination = int(np.argmax(score))
            door = central_door(env, doors)
        else:
            destination = int(np.argmax(waiting))
            door = nearest_door_to_lots(env, doors, destination)
        return truck, door, destination


class CyclicPlanPolicy:
    """Cycle-wise static planning with VAA (`iterations=0`) or VAA-GILS.

    The plan fixes each truck's destination and the dispatch order (cycle by
    cycle; compound trucks first, then outbound trucks in door-sequence order).
    `execution="strict"` waits for the planned door. `execution="adaptive"`
    (default) uses the planned door when free and otherwise the free door
    closest to it, and releases an outbound truck only after every compound
    truck of its cycle that carries freight for its destination has docked, so
    the carrier claims that freight as the static model assumes.
    """

    def __init__(self, *, iterations: int = 1000, seed: int = 0, execution: str = "adaptive") -> None:
        if execution not in ("adaptive", "strict"):
            raise ValueError("execution must be 'adaptive' or 'strict'")
        self.iterations = iterations
        self.seed = seed
        self.execution = execution
        base = "Cyclic-VAA" if iterations == 0 else "Cyclic-GILS"
        self.name = base if execution == "adaptive" else f"{base}-strict"

    def reset(self, env: CrossDockStream) -> None:
        self._pending: list[Truck] = []
        self._plan: list[tuple[Truck, int, int, list[Truck]]] = []
        self._seen = -1
        self._cycle = 0
        self.plan_seconds: list[float] = []
        self.cycle_wait: list[float] = []

    def act(self, env: CrossDockStream):
        for truck in env.yard:
            if truck.uid > self._seen:
                self._pending.append(truck)
                self._seen = truck.uid
        size = env.config.num_destinations
        while len(self._pending) >= size:
            cycle, self._pending = self._pending[:size], self._pending[size:]
            self._plan_cycle(env, cycle)

        free = env.free_doors()
        travel = env.facility.travel
        for index, (truck, destination, door, gate) in enumerate(self._plan):
            if self.execution == "strict":
                if door not in free or any(other.door == door and other is not truck and other in env.yard
                                           for other, _, _, _ in self._plan[:index]):
                    continue
                chosen = door
            else:
                if any(t.dock_time != t.dock_time for t in gate if t.units[destination] > 0):
                    continue  # a same-cycle source of this destination has not docked yet
                chosen = door if door in free else min(free, key=lambda m: (travel[door, m], m))
            del self._plan[index]
            return truck, chosen, destination
        return None

    def _plan_cycle(self, env: CrossDockStream, cycle: list[Truck]) -> None:
        start = time.perf_counter()
        compounds = [t for t in cycle if t.compound]
        outbounds = [t for t in cycle if not t.compound]
        entries: list[tuple[Truck, int, int, list[Truck]]] = []
        if compounds:
            instance = cycle_instance(env, compounds, outbounds, env.now)
            if self.iterations > 0:
                solution = run_vaa_qrl(
                    instance,
                    VaaQRLConfig(
                        max_iterations=self.iterations,
                        tardiness_weight=env.config.tardiness_weight,
                        seed=self.seed * 100_003 + self._cycle,
                        use_sa_acceptance=False,
                    ),
                    selector=UniformSelector(ACTIONS_TW),
                ).solution
            else:
                solution = vaa_solution(instance)
            by_name = {f"T{t.uid}": t for t in cycle}
            for name, (dest, door) in sorted(solution.compound_assignment.items(), key=lambda kv: kv[1][1]):
                entries.append((by_name[name], int(dest[1:]), door, []))
            ordered = sorted(
                (position, door, name)
                for door, sequence in solution.door_sequences.items()
                for position, name in enumerate(sequence)
            )
            for _, door, name in ordered:
                dest, _ = solution.outbound_assignment[name]
                entries.append((by_name[name], int(dest[1:]), door, compounds))
        else:
            # No inbound freight in this cycle: one outbound per destination,
            # largest backlog first, spread over doors.
            order = np.argsort(-backlog_handling(env))
            for slot, (truck, destination) in enumerate(zip(outbounds, order)):
                entries.append((truck, int(destination), slot % env.config.num_doors, []))
        self._plan.extend(entries)
        complete = max(t.arrival for t in cycle)
        self.cycle_wait.extend(complete - t.arrival for t in cycle)
        self.plan_seconds.append(time.perf_counter() - start)
        self._cycle += 1


def cycle_instance(
    env: CrossDockStream,
    compounds: list[Truck],
    outbounds: list[Truck],
    formed: float,
) -> CrossDockInstance:
    """Static instance of one cycle, times relative to the cycle formation time.

    Every truck has arrived (release 0); due dates keep the remaining SLA slack.
    Door availability is not part of the static model and is ignored here.
    """

    cfg = env.config
    fac = env.facility
    trucks = [*compounds, *outbounds]
    names = {t.uid: f"T{t.uid}" for t in trucks}
    destinations = [f"D{d}" for d in range(cfg.num_destinations)]
    flow = np.zeros((len(compounds), cfg.num_destinations, cfg.num_products))
    # Units per destination are split evenly over products; handling must match
    # the stream exactly, so rebuild flow from handling with unit product time
    # weights scaled to reproduce handling per destination.
    for i, truck in enumerate(compounds):
        for d in range(cfg.num_destinations):
            if truck.units[d] > 0:
                flow[i, d, 0] = truck.handling[d]
    product_time = np.zeros(cfg.num_products)
    product_time[0] = 1.0
    return CrossDockInstance(
        compound_trucks=[names[t.uid] for t in compounds],
        outbound_trucks=[names[t.uid] for t in outbounds],
        destinations=destinations,
        doors=list(range(cfg.num_doors)),
        product_types=[f"K{k}" for k in range(cfg.num_products)],
        flow=flow,
        product_time=product_time,
        travel_time=fac.travel,
        enter_time={names[t.uid]: t.enter for t in trucks},
        leave_time={names[t.uid]: t.leave for t in trucks},
        release_time={names[t.uid]: 0.0 for t in trucks},
        due_time={names[t.uid]: t.due - formed for t in trucks},
    )
