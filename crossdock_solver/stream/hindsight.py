"""Hindsight-optimal schedule of a finite truck set (CP-SAT).

Generalized static model: any number of trucks may serve a destination
(|I| + |F| >> |D|), every arrival is known in advance, and the simulator's
mechanics are reproduced exactly:

- truck j docks at s_j >= a_j on door m_j and retains / serves destination d_j;
  a compound truck's lots for the other destinations are ready at
  u_j = s_j + enter_j + (total_j - h_j(d_j)), which is also its claim time c_j;
  an outbound truck claims at c_j = s_j + enter_j,
- claim rule: lot (i, d) goes to the carrier of d with the earliest claim time
  c_k >= s_i (the lot joins the open lots when i docks),
- carrier j leaves at e_j = max(c_j, max_i u_i + travel(m_i, m_j)) + sum_i h_i(d) + leave_j,
- doors hold one truck at a time over [s_j, e_j),
- freight no truck carries goes to the terminal sweeper of its destination,
  which claims at Cmax (the last truck departure) and leaves after loading +
  SWEEP_LEAVE (finite.py),
- J = sum(units * (carrier departure - arrival)) / units + lambda * mean tardiness.

Times are integers in 1/100 time units (`SCALE`), which is exact for a
`FiniteInstance`. `evaluate_schedule` fixes a simulator run's decisions to
check that the model and the simulator agree.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time

import numpy as np

from crossdock_solver.exact.cpsat import cp_model  # applies the pandas/pyarrow stub first
from crossdock_solver.stream.finite import SWEEP_LEAVE, FiniteInstance

SCALE = 100


@dataclass
class HindsightResult:
    objective: float  # best schedule found, J units
    bound: float  # CP-SAT lower bound, J units
    optimal: bool
    status: str
    seconds: float
    dock: list[float]
    door: list[int]
    destination: list[int]
    departure: list[float]

    @property
    def gap(self) -> float:
        return (self.objective - self.bound) / self.objective if self.objective > 0 else 0.0


def _ticks(x: float) -> int:
    return int(round(x * SCALE))


@dataclass
class ModelData:
    """Input of the CP-SAT model, times in ticks. Besides a finite instance it
    can describe a live simulator state (rolling horizon, rolling.py):

    - `release[j]`: earliest dock time (the decision time for yard trucks),
    - `fixed[j]`: decisions already taken, {"dock", "door", "destination"} and
      optionally "departure" (known once the truck claimed; its departure
      constraints are then dropped),
    - `lots[i, d]`: -1 if the lot no longer concerns the model (carried away),
      j if carrier j already claimed it; missing = decided by the model,
    - `claims_new[j]`: False for trucks that can no longer claim (claimed already),
    - `counts[j]`: whether j's tardiness and retained units enter the objective,
    - `norm`: (trucks, units) normalizing J,
    - `sweep_delay`: extra wait before the terminal sweeper claims (0 for a
      finite instance; a rolling horizon uses it as the expected wait for a
      future carrier, otherwise stranded freight would look cheap).
    """

    a: list[int]
    due: list[int]
    enter: list[int]
    leave: list[int]
    units: list[list[int]]
    h: list[list[int]]
    compound: list[bool]
    travel: list[list[int]]
    weight: float
    release: list[int]
    fixed: list[dict | None]
    lots: dict[tuple[int, int], int]
    claims_new: list[bool]
    counts: list[bool]
    norm: tuple[int, int]
    sweep_delay: int = 0

    @property
    def size(self) -> tuple[int, int, int]:
        return len(self.a), len(self.units[0]), len(self.travel)


def instance_data(instance: FiniteInstance) -> ModelData:
    cfg = instance.config
    fac = instance.facility
    trucks = instance.trucks
    N, M = len(trucks), cfg.num_doors
    units = [[int(round(u)) for u in t.units] for t in trucks]
    return ModelData(
        a=[_ticks(t.arrival) for t in trucks],
        due=[_ticks(round(t.arrival + fac.sla, 2)) for t in trucks],
        enter=[_ticks(t.enter) for t in trucks],
        leave=[_ticks(t.leave) for t in trucks],
        units=units,
        h=[[_ticks(x) for x in t.handling] for t in trucks],
        compound=[t.compound for t in trucks],
        travel=[[_ticks(fac.travel[m, k]) for k in range(M)] for m in range(M)],
        weight=cfg.tardiness_weight,
        release=[0] * N,
        fixed=[None] * N,
        lots={},
        claims_new=[True] * N,
        counts=[True] * N,
        norm=(N, sum(map(sum, units))),
    )


def solve_hindsight(
    instance: FiniteInstance,
    *,
    time_limit: float = 60.0,
    workers: int = 1,
    hint: dict | None = None,
    fix: dict | None = None,
    seed: int = 0,
    relax_doors: bool = False,
    relax_claim: bool = False,
    event_aligned: bool = False,
) -> HindsightResult:
    """`hint`/`fix`: {"dock": [...], "door": [...], "destination": [...]} per truck.

    `relax_doors=True` drops door identities: the doors become a capacity of
    |M| simultaneous trucks and travel times are zero. Every schedule of the
    full model stays feasible at no higher cost, so its optimum (or CP-SAT
    bound) is a valid lower bound on the hindsight optimum, and it is much
    easier to prove. `relax_claim=True` also lets a lot go to any carrier of
    its destination that claims after the source docked (not only the
    earliest one), another relaxation.

    `event_aligned=True` restricts every dock time to an arrival or a departure
    time, the only moments at which the simulator asks the policy for a
    decision. The model then has exactly the action space of the online
    policies (with perfect information); without it, a truck may also dock at
    any moment in between (e.g. just after some carrier claimed), which no
    event-driven policy can do.
    """

    return solve_model(instance_data(instance), time_limit=time_limit, workers=workers, hint=hint, fix=fix,
                       seed=seed, relax_doors=relax_doors, relax_claim=relax_claim, event_aligned=event_aligned)


def solve_model(
    data: ModelData,
    *,
    time_limit: float = 60.0,
    workers: int = 1,
    hint: dict | None = None,
    fix: dict | None = None,
    seed: int = 0,
    relax_doors: bool = False,
    relax_claim: bool = False,
    event_aligned: bool = False,
) -> HindsightResult:
    N, D, M = data.size
    a, due, enter, leave, units, h = data.a, data.due, data.enter, data.leave, data.units, data.h
    compound, travel = data.compound, data.travel
    flat_travel = [travel[m][k] for m in range(M) for k in range(M)]
    total = [sum(row) for row in h]
    fixed_departures = [f["departure"] for f in data.fixed if f is not None and f.get("departure") is not None]
    horizon = (max([*a, *data.release, *fixed_departures]) + sum(enter) + sum(leave) + 2 * sum(total)
               + max(flat_travel) * N + 1)
    far = 2 * horizon + data.sweep_delay  # latest possible freight departure (sweeper)

    model = cp_model.CpModel()
    s = [model.NewIntVar(max(a[j], data.release[j]), horizon, f"s{j}") for j in range(N)]
    e = [model.NewIntVar(a[j], horizon, f"e{j}") for j in range(N)]
    c = [model.NewIntVar(a[j], horizon, f"c{j}") for j in range(N)]
    y = [[model.NewBoolVar(f"y{j}_{d}") for d in range(D)] for j in range(N)]
    z = [[model.NewBoolVar(f"z{j}_{m}") for m in range(M)] for j in range(N)] if not relax_doors else []
    door = [model.NewIntVar(0, M - 1, f"m{j}") for j in range(N)] if not relax_doors else []
    for j in range(N):
        model.AddExactlyOne(y[j])
        if not relax_doors:
            model.AddExactlyOne(z[j])
            model.Add(door[j] == sum(m * z[j][m] for m in range(M)))
        unload = sum((total[j] - h[j][d]) * y[j][d] for d in range(D)) if compound[j] else 0
        model.Add(c[j] == s[j] + enter[j] + unload)
        f = data.fixed[j]
        if f is not None:
            model.Add(s[j] == f["dock"])
            model.Add(y[j][f["destination"]] == 1)
            if not relax_doors:
                model.Add(z[j][f["door"]] == 1)
            if f.get("departure") is not None:
                model.Add(e[j] == f["departure"])
    if relax_doors:
        spans = [model.NewIntervalVar(s[j], model.NewIntVar(0, horizon, f"p{j}"), e[j], f"iv{j}") for j in range(N)]
        model.AddCumulative(spans, [1] * N, M)
    for m in range(M if not relax_doors else 0):
        intervals = []
        for j in range(N):
            size = model.NewIntVar(0, horizon, f"p{j}_{m}")
            intervals.append(model.NewOptionalIntervalVar(s[j], size, e[j], z[j][m], f"iv{j}_{m}"))
        model.AddNoOverlap(intervals)

    if event_aligned:
        for j in range(N):
            if data.fixed[j] is not None:
                continue  # already docked (at an event of a truck possibly no longer modelled)
            options = []
            for k in range(N):
                at_arrival = model.NewBoolVar(f"ea{j}_{k}")
                model.Add(s[j] == a[k]).OnlyEnforceIf(at_arrival)
                options.append(at_arrival)
                if k != j:
                    at_departure = model.NewBoolVar(f"ed{j}_{k}")
                    model.Add(s[j] == e[k]).OnlyEnforceIf(at_departure)
                    options.append(at_departure)
            if data.release[j] > 0:  # the current decision time (rolling horizon)
                at_release = model.NewBoolVar(f"er{j}")
                model.Add(s[j] == data.release[j]).OnlyEnforceIf(at_release)
                options.append(at_release)
            model.AddBoolOr(options)

    # claim-order literals b[i][k] <=> c_k >= s_i (for carriers that can still claim)
    sources = [i for i in range(N) if compound[i]]
    carriers = [k for k in range(N) if data.claims_new[k]]
    b: dict[tuple[int, int], cp_model.IntVar] = {}
    for i in sources:
        for k in carriers:
            if k == i:
                continue
            lit = model.NewBoolVar(f"b{i}_{k}")
            model.Add(c[k] >= s[i]).OnlyEnforceIf(lit)
            model.Add(c[k] < s[i]).OnlyEnforceIf(lit.Not())
            b[i, k] = lit

    load = [[] for _ in range(N)]  # (bool or 1, handling) claimed by carrier j
    min_leave = min(leave)
    cmax = model.NewIntVar(max(a), horizon, "cmax")
    model.AddMaxEquality(cmax, e)
    sweep_load = [[] for _ in range(D)]
    sweep_depart = [model.NewIntVar(0, far, f"sweep{d}") for d in range(D)]
    lead_terms = []
    x: dict[tuple[int, int, int], object] = {}
    for i in sources:
        for d in range(D):
            if units[i][d] == 0:
                continue
            status = data.lots.get((i, d))
            depart = model.NewIntVar(a[i], far, f"F{i}_{d}")
            if status is not None:
                # lot already carried away (-1) or claimed by carrier `status`
                if status >= 0:
                    model.Add(y[i][d] == 0)
                    x[i, d, status] = 1
                    load[status].append((1, h[i][d]))
                    model.Add(depart >= e[status])
                    lead_terms.append((units[i][d], depart, i))
                continue
            lot = y[i][d].Not()  # the lot exists unless i retains d
            options = []
            for j in carriers:
                if j == i:
                    continue
                v = model.NewBoolVar(f"x{i}_{d}_{j}")
                model.AddImplication(v, y[j][d])
                model.AddImplication(v, b[i, j])
                x[i, d, j] = v
                options.append((j, v))
                load[j].append((v, h[i][d]))
            sweep = model.NewBoolVar(f"x{i}_{d}_sweep")
            sweep_load[d].append((sweep, h[i][d]))
            model.Add(sum(v for _, v in options) + sweep == 1).OnlyEnforceIf(lot)
            model.AddImplication(y[i][d], sweep.Not())
            model.Add(sum(v for _, v in options) == 0).OnlyEnforceIf(y[i][d])
            # earliest-claim rule
            claim = model.NewIntVar(0, horizon, f"C{i}_{d}")
            for j, v in options if not relax_claim else []:
                model.Add(claim == c[j]).OnlyEnforceIf(v)
                model.Add(claim <= c[j]).OnlyEnforceIf([y[j][d], b[i, j], lot])
            # F: departure of the units (i, d), with i (retained) or with their carrier
            model.Add(depart >= e[i]).OnlyEnforceIf(y[i][d])
            for j, v in options:
                model.Add(depart >= e[j]).OnlyEnforceIf(v)
            # the sweeper claims at Cmax, after every real carrier (so the
            # earliest-claim rule picks it only when no real carrier is left)
            model.Add(claim == cmax).OnlyEnforceIf(sweep)
            model.Add(depart >= sweep_depart[d]).OnlyEnforceIf(sweep)
            if data.counts[i]:
                # valid either way (strengthens the relaxation): leave with i, or be
                # loaded (>= own handling) onto a carrier that then exits
                model.Add(depart >= c[i] + min(leave[i], h[i][d] + min_leave))
                lead_terms.append((units[i][d], depart, i))
            else:
                # i has left: its retained units are gone, only the lot counts
                model.Add(depart >= c[i] + h[i][d] + min_leave).OnlyEnforceIf(lot)
                counted = model.NewIntVar(0, far, f"G{i}_{d}")
                model.Add(counted >= depart).OnlyEnforceIf(lot)
                lead_terms.append((units[i][d], counted, i))

    for j in range(N):
        f = data.fixed[j]
        if f is not None and f.get("departure") is not None:
            continue  # known departure
        claimed = sum(v * hd for v, hd in load[j]) if load[j] else 0
        model.Add(e[j] >= c[j] + claimed + leave[j])
        for i in sources:
            if i == j:
                continue
            used = [x[i, d, j] for d in range(D) if (i, d, j) in x]
            if not used:
                continue
            if relax_doors:
                t = 0
            else:
                t = model.NewIntVar(0, max(flat_travel), f"t{i}_{j}")
                model.AddElement(door[i] * M + door[j], flat_travel, t)
            if all(isinstance(u, int) for u in used):
                model.Add(e[j] >= c[i] + t + claimed + leave[j])
                continue
            any_used = model.NewBoolVar(f"w{i}_{j}")
            model.AddMaxEquality(any_used, used)
            # u_i = c_i for a compound truck
            model.Add(e[j] >= c[i] + t + claimed + leave[j]).OnlyEnforceIf(any_used)

    for d in range(D):
        loaded = sum(v * hd for v, hd in sweep_load[d]) if sweep_load[d] else 0
        model.Add(sweep_depart[d] >= cmax + data.sweep_delay + loaded + _ticks(SWEEP_LEAVE))

    # objective: n * sum(units * lead) + lambda * U * sum(tardiness)   (ticks)
    n, U = data.norm
    obj = [u * depart for u, depart, _ in lead_terms]
    constant = sum(u * a[i] for u, _, i in lead_terms)
    tard = []
    for j in range(N):
        if not data.counts[j]:
            continue
        t = model.NewIntVar(0, horizon, f"T{j}")
        model.Add(t >= e[j] - due[j])
        tard.append(t)
    # integer weights: lambda * U as a rational with denominator 1000
    lam = int(round(data.weight * 1000))
    model.Minimize(1000 * n * sum(obj) + lam * U * sum(tard))
    scale_obj = 1000 * n * U * SCALE

    def _apply(values: dict, strict: bool) -> None:
        add = (lambda var, val: model.Add(var == val)) if strict else model.AddHint
        for j in range(N):
            add(s[j], _ticks(values["dock"][j]))
            for m in range(M if not relax_doors else 0):
                add(z[j][m], int(values["door"][j] == m))
            for d in range(D):
                add(y[j][d], int(values["destination"][j] == d))

    if fix is not None:
        _apply(fix, True)
    elif hint is not None:
        _apply(hint, False)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    start = time.perf_counter()
    status = solver.Solve(model)
    seconds = time.perf_counter() - start
    name = solver.StatusName(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return HindsightResult(math.inf, 0.0, False, name, seconds, [], [], [], [])
    off = 1000 * n * constant
    value = (solver.ObjectiveValue() - off) / scale_obj
    bound = (solver.BestObjectiveBound() - off) / scale_obj
    return HindsightResult(
        objective=value,
        bound=max(bound, 0.0),
        optimal=status == cp_model.OPTIMAL,
        status=name,
        seconds=seconds,
        dock=[solver.Value(v) / SCALE for v in s],
        door=[solver.Value(v) for v in door] if not relax_doors else [-1] * N,
        destination=[int(np.argmax([solver.Value(v) for v in row])) for row in y],
        departure=[solver.Value(v) / SCALE for v in e],
    )


def schedule_of(env) -> dict:
    """Decisions of a finished `FiniteStream` run, by truck uid."""

    trucks = sorted([*env.departed, *env.in_system, *env.yard], key=lambda t: t.uid)
    trucks = list({t.uid: t for t in trucks if t.uid >= 0}.values())  # sweepers have negative uids
    return {
        "dock": [t.dock_time for t in trucks],
        "door": [t.door for t in trucks],
        "destination": [t.destination for t in trucks],
    }


def evaluate_schedule(instance: FiniteInstance, schedule: dict, time_limit: float = 30.0) -> HindsightResult:
    """Objective of a fixed schedule under the model (should equal the simulator's)."""

    return solve_hindsight(instance, fix=schedule, time_limit=time_limit)
