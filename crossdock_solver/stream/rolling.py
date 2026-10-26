"""Rolling-horizon re-optimization baseline for the continuous cross-dock.

At every decision the current state is turned into the generalized static
model of `hindsight.py` (any number of carriers per destination) and solved by
CP-SAT under a short time limit:

- trucks: the docked ones (decisions fixed; departure fixed once they claimed),
  the first `max_yard` yard trucks (free, dock time >= now) and the sources of
  every lot still in the dock (fixed, their own cost already sunk),
- no future arrivals are assumed (the information an online method has);
  freight no modelled truck can carry goes to the terminal sweeper, which
  makes the plan prefer carrying open freight with the trucks at hand,
- the yard trucks the plan docks now are dispatched (planned door and
  destination); if the plan docks nobody now the policy holds until the next
  event, where it re-optimizes. If CP-SAT finds no schedule in time the
  FCFS-VAA action is taken.

Times are rounded to the model's 0.01 grid, so the plan is approximate; the
simulator executes the actions exactly.
"""

from __future__ import annotations

import math

from crossdock_solver.stream.hindsight import ModelData, _ticks, solve_model
from crossdock_solver.stream.policies import FCFSRulePolicy
from crossdock_solver.stream.sim import CrossDockStream, Truck


def state_data(env: CrossDockStream, max_yard: int, sweep_delay=0.0) -> tuple[ModelData, list[Truck]]:
    """`sweep_delay`: one delay or one per destination (time units)."""
    docked = [t for t in env.doors if t is not None]
    yard = env.yard[:max_yard]
    trucks: dict[int, Truck] = {t.uid: t for t in [*docked, *yard]}
    for lots in env.open_lots:
        for lot in lots:
            trucks.setdefault(lot.source.uid, lot.source)
    for carrier in docked:
        for lot in carrier.lots:
            trucks.setdefault(lot.source.uid, lot.source)
    order = sorted(trucks.values(), key=lambda t: t.uid)
    index = {t.uid: k for k, t in enumerate(order)}
    yard_ids = {t.uid for t in yard}
    open_ids = {(lot.source.uid, d) for d, lots in enumerate(env.open_lots) for lot in lots}
    claimed_by = {(lot.source.uid, lot.destination): index[c.uid] for c in docked for lot in c.lots}
    now = _ticks(env.now)

    fixed, claims_new, counts, lots = [], [], [], {}
    for k, t in enumerate(order):
        departed = not math.isnan(t.departure)
        if t.uid in yard_ids:
            fixed.append(None)
            claims_new.append(True)
        else:
            claimed = not math.isnan(t.claim_time)
            departure = t.departure if departed else (t.expected_departure if claimed else None)
            fixed.append({"dock": _ticks(t.dock_time), "door": t.door, "destination": t.destination,
                          "departure": None if departure is None else _ticks(departure)})
            claims_new.append(not claimed)
            if t.compound:
                for d in range(len(t.units)):
                    if d == t.destination or t.units[d] == 0:
                        continue
                    if (t.uid, d) in open_ids:
                        continue  # still open: the model picks its carrier
                    lots[k, d] = claimed_by.get((t.uid, d), -1)
        counts.append(not departed)
    D = env.config.num_destinations
    data = ModelData(
        a=[_ticks(t.arrival) for t in order],
        due=[_ticks(t.due) for t in order],
        enter=[_ticks(t.enter) for t in order],
        leave=[_ticks(t.leave) for t in order],
        units=[[int(round(u)) for u in t.units] for t in order],
        h=[[_ticks(x) for x in t.handling] for t in order],
        compound=[t.compound for t in order],
        travel=[[_ticks(x) for x in row] for row in env.facility.travel],
        weight=env.config.tardiness_weight,
        release=[now if t.uid in yard_ids else 0 for t in order],
        fixed=fixed,
        lots=lots,
        claims_new=claims_new,
        counts=counts,
        norm=(max(1, sum(counts)), max(1, int(sum(t.units.sum() for t in order)))),
        sweep_delay=[_ticks(x) for x in sweep_delay] if hasattr(sweep_delay, "__len__") else _ticks(sweep_delay),
    )
    assert D == len(data.units[0])
    return data, order


class RollingHorizonPolicy:
    def __init__(self, *, time_limit: float = 1.0, max_yard: int = 8, workers: int = 1,
                 event_aligned: bool = True, terminal: float = 1.0, terminal_model=None,
                 name: str = "Rolling-CPSAT") -> None:
        self.time_limit = time_limit
        self.terminal = terminal  # sweeper delay in units of (|D| interarrival times + mean truck work)
        # optional learned per-destination delay (terminal.py): callable(env, max_yard) -> delays (time units)
        self.terminal_model = terminal_model
        self.event_aligned = event_aligned
        self.max_yard = max_yard
        self.workers = workers
        self.name = name
        self._fallback = FCFSRulePolicy()

    def reset(self, env: CrossDockStream) -> None:
        self._plan_time = None
        self._plan: list[tuple[int, int, int]] = []
        self.solves = 0
        self.fallbacks = 0
        self.optimal = 0

    def act(self, env: CrossDockStream):
        if self._plan_time != env.now:
            self._replan(env)
        free = set(env.free_doors())
        yard = {t.uid: t for t in env.yard}
        for k, (uid, door, destination) in enumerate(self._plan):
            if uid in yard and door in free:
                del self._plan[k]
                return yard[uid], door, destination
        return None  # nobody docks now: hold until the next event

    def _replan(self, env: CrossDockStream) -> None:
        self._plan_time = env.now
        self._plan = []
        fac = env.facility
        if self.terminal_model is not None:
            delay = self.terminal_model(env, self.max_yard)
        else:
            delay = self.terminal * (env.config.num_destinations / fac.arrival_rate + fac.mean_work)
        data, order = state_data(env, self.max_yard, delay)
        result = solve_model(data, time_limit=self.time_limit, workers=self.workers, event_aligned=self.event_aligned)
        self.solves += 1
        self.optimal += result.optimal
        if not result.dock:
            self.fallbacks += 1
            truck, door, destination = self._fallback.act(env)
            self._plan = [(truck.uid, door, destination)]
            return
        now = _ticks(env.now)
        yard_ids = {t.uid for t in env.yard[: self.max_yard]}
        starts = sorted(
            (k for k, t in enumerate(order) if t.uid in yard_ids and _ticks(result.dock[k]) <= now),
            key=lambda k: order[k].uid,
        )
        self._plan = [(order[k].uid, result.door[k], result.destination[k]) for k in starts]
