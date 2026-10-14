"""Reference policies for the continuous cross-dock.

- `FCFSRulePolicy`: work-conserving dispatching. The earliest yard truck goes to
  a free door. A compound truck retains the destination with the most own
  handling (the per-truck essence of the VAA regret rule) or, with
  `backlog=True`, own handling plus the waiting backlog; an outbound truck
  serves the destination with the largest claimable backlog.
- `SPTRulePolicy`: shortest-processing-time sequencing among the front yard
  trucks, with the FCFS-VAA destination and door rules.
- `RandomPolicy`: a random front yard truck, free door and destination (no hold).
- `PriorityRulePolicy`: a linear priority rule over interpretable (truck,
  destination) features with a hold threshold; its weights are tuned
  (experiments/stream_rule_tune.py) and it serves as the tuned-rule baseline.
- `CyclicPlanPolicy`: the static method applied as-is. Its model needs exactly
  one carrier per destination, so arriving trucks are grouped first-come
  first-served into cycles of |D| trucks (|I_c| + |F_c| = |D|), each cycle is
  solved as a static instance by VAA, VAA-GILS, the original paper's SA-RL5
  or CP-SAT, and the plan is executed door by door (compound first, then the
  outbound sequence).
"""

from __future__ import annotations

import time

import numpy as np

from crossdock_solver.baselines.paper_sa_rl import PaperSARLConfig, run_paper_sa_rl
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


class SPTRulePolicy:
    """Shortest processing time first among the front yard trucks.

    Processing time is the truck's own door work: entry + exit + its freight
    handling for a compound truck, entry + exit + the backlog it would claim
    for an outbound truck. Destination and door follow FCFS-VAA. (EDD equals
    FCFS here because every due date is arrival + the same SLA.)
    """

    name = "SPT-VAA"

    def act(self, env: CrossDockStream):
        doors = env.free_doors()
        waiting = backlog_handling(env)
        top = float(waiting.max())

        def work(truck: Truck) -> float:
            own = float(truck.handling.sum()) if truck.compound else top
            return truck.enter + truck.leave + own

        truck = min(env.yard[: env.max_candidates], key=lambda t: (work(t), t.uid))
        if truck.compound:
            destination = int(np.argmax(truck.handling))
            door = central_door(env, doors)
        else:
            destination = int(np.argmax(waiting))
            door = nearest_door_to_lots(env, doors, destination)
        return truck, door, destination


class RandomPolicy:
    """Uniformly random (front yard truck, free door, destination); never holds."""

    name = "Random"

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed

    def reset(self, env: CrossDockStream) -> None:
        self._rng = np.random.default_rng(self.seed * 100_003 + env.seed)

    def act(self, env: CrossDockStream):
        rng = self._rng
        trucks = env.yard[: env.max_candidates]
        doors = env.free_doors()
        truck = trucks[int(rng.integers(len(trucks)))]
        return truck, doors[int(rng.integers(len(doors)))], int(rng.integers(env.config.num_destinations))


PRIORITY_FEATURES = (
    "wait",  # time the truck has waited in the yard
    "slack",  # time left until the truck's due date
    "own_share",  # share of the truck's own freight bound for d (compound only)
    "backlog",  # handling of unclaimed lots for d
    "oldest",  # age of the oldest unclaimed lot for d
    "since_last",  # time since the last departure to d
    "outbound",  # 1 for an outbound truck
    "work",  # the truck's own door work if it serves d (unload of the rest, or the claimable backlog)
    "unready",  # handling of lots for d still being unloaded (the carrier would wait at the door)
)


class PriorityRulePolicy:
    """Score every (front yard truck, destination) by a weighted sum of
    PRIORITY_FEATURES (times in units of the mean truck work), dispatch the best
    one to the rule door, or hold when the best score is below `threshold`."""

    def __init__(self, weights, threshold: float = -np.inf, name: str = "Tuned-Rule") -> None:
        self.weights = np.asarray(weights, dtype=float)
        if self.weights.shape != (len(PRIORITY_FEATURES),):
            raise ValueError(f"need {len(PRIORITY_FEATURES)} weights")
        self.threshold = float(threshold)
        self.name = name

    def features(self, env: CrossDockStream, trucks: list[Truck]) -> np.ndarray:
        work = env.facility.mean_work
        now = env.now
        D = env.config.num_destinations
        backlog = backlog_handling(env)
        oldest = np.zeros(D)
        unready = np.zeros(D)
        for d, lots in enumerate(env.open_lots):
            if lots:
                oldest[d] = now - min(lot.source.arrival for lot in lots)
                unready[d] = sum(lot.handling for lot in lots if lot.ready > now)
        since_last = now - env.last_departure
        out = np.zeros((len(trucks), D, len(PRIORITY_FEATURES)))
        for i, truck in enumerate(trucks):
            total = float(truck.handling.sum())
            f = out[i]
            f[:, 0] = now - truck.arrival
            f[:, 1] = truck.due - now
            f[:, 2] = truck.handling / total if truck.compound and total > 0 else 0.0
            f[:, 3] = backlog
            f[:, 4] = oldest
            f[:, 5] = since_last
            f[:, 6] = 0.0 if truck.compound else 1.0
            f[:, 7] = truck.enter + truck.leave + ((total - truck.handling) if truck.compound else backlog)
            f[:, 8] = unready
        out[..., [0, 1, 3, 4, 5, 7, 8]] /= work
        return out

    def act(self, env: CrossDockStream):
        trucks = env.yard[: env.max_candidates]
        scores = self.features(env, trucks) @ self.weights  # (T, D)
        i, d = np.unravel_index(int(np.argmax(scores)), scores.shape)
        if scores[i, d] < self.threshold:
            return None
        truck = trucks[i]
        doors = env.free_doors()
        door = central_door(env, doors) if truck.compound else nearest_door_to_lots(env, doors, int(d))
        return truck, door, int(d)


CYCLIC_SOLVERS = {"vaa": "Cyclic-VAA", "gils": "Cyclic-GILS", "sa-rl5": "Cyclic-SA-RL5", "cpsat": "Cyclic-CPSAT"}


class CyclicPlanPolicy:
    """Cycle-wise static planning with VAA (`iterations=0`) or VAA-GILS.

    `solver` overrides the choice: "sa-rl5" runs the original paper's SA-RL5
    (Q-learning neighbourhood selection + SA acceptance, objective makespan +
    lambda * tardiness, i.e. Extended-SA-RL5 of the JKIIE study) for
    `iterations` iterations; "cpsat" solves each cycle with CP-SAT
    (`cpsat_time_limit` seconds, falling back to VAA-GILS when no incumbent).

    The plan fixes each truck's destination and the dispatch order (cycle by
    cycle; compound trucks first, then outbound trucks in door-sequence order).
    `execution="strict"` waits for the planned door. `execution="adaptive"`
    (default) uses the planned door when free and otherwise the free door
    closest to it, and releases an outbound truck only after every compound
    truck of its cycle that carries freight for its destination has docked, so
    the carrier claims that freight as the static model assumes.
    """

    def __init__(
        self,
        *,
        iterations: int = 1000,
        seed: int = 0,
        execution: str = "adaptive",
        solver: str | None = None,
        cpsat_time_limit: float = 10.0,
    ) -> None:
        if execution not in ("adaptive", "strict"):
            raise ValueError("execution must be 'adaptive' or 'strict'")
        solver = solver or ("vaa" if iterations == 0 else "gils")
        if solver not in CYCLIC_SOLVERS:
            raise ValueError(f"solver must be one of {sorted(CYCLIC_SOLVERS)}")
        self.iterations = iterations
        self.seed = seed
        self.execution = execution
        self.solver = solver
        self.cpsat_time_limit = cpsat_time_limit
        base = CYCLIC_SOLVERS[solver]
        self.name = base if execution == "adaptive" else f"{base}-strict"

    def reset(self, env: CrossDockStream) -> None:
        self._pending: list[Truck] = []
        self._plan: list[tuple[Truck, int, int, list[Truck]]] = []
        self._seen = -1
        self._cycle = 0
        self.plan_seconds: list[float] = []
        self.cycle_wait: list[float] = []
        self.cpsat_optimal = 0  # cycles CP-SAT proved optimal (solver="cpsat")

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
            solution = self._solve(instance, env.config.tardiness_weight)
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

    def _solve(self, instance: CrossDockInstance, weight: float):
        seed = self.seed * 100_003 + self._cycle
        if self.solver == "vaa":
            return vaa_solution(instance)
        if self.solver == "sa-rl5":
            return run_paper_sa_rl(
                instance,
                PaperSARLConfig(
                    max_iterations=self.iterations,
                    tardiness_weight=weight,
                    seed=seed,
                    name="Extended-SA-RL5",
                ),
            ).solution
        gils = lambda: run_vaa_qrl(  # noqa: E731
            instance,
            VaaQRLConfig(
                max_iterations=self.iterations,
                tardiness_weight=weight,
                seed=seed,
                use_sa_acceptance=False,
            ),
            selector=UniformSelector(ACTIONS_TW),
        ).solution
        if self.solver == "gils":
            return gils()
        from crossdock_solver.exact.cpsat import ExactCPSATConfig, solve_exact_cpsat

        exact = solve_exact_cpsat(
            instance,
            ExactCPSATConfig(time_limit_sec=self.cpsat_time_limit, workers=1, tardiness_weight=weight),
        )
        self.cpsat_optimal += exact.proven_optimal
        return exact.run.solution if exact.run is not None else gils()


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
