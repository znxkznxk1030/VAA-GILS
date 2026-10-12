"""Toy example: why release times + soft due dates change the compound-truck problem.

Three compound trucks share two destinations (D1, D2); D3 is a small third
destination so that |I| + |F| = |D| holds (every truck retains exactly one
destination). Three doors on a line. Every feasible solution (3! retained
destinations x 3! door assignments = 36) is enumerated with the evaluator, and
the optimum is confirmed with CP-SAT.

Settings
    base      : r_q = 0, no due dates, objective = makespan (Shahmardan & Sajadieh 2020)
    extended  : r = (0, 0, R3), soft due d_q, objective = makespan + lambda * tardiness (this study)

Reported
    1. base vs extended optimum (retained destinations, makespan, tardiness)
    2. the base-optimal plan evaluated in the extended setting (cost of ignoring time windows)
    3. delay propagation: R3 = 0..40 with the plan fixed, finish time of every truck
    4. robustness: share of random small instances whose base-optimal retained
       destinations are no longer optimal once release times and due dates apply

Usage:
    python experiments/novelty_toy_example.py
"""

from __future__ import annotations

import itertools
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from crossdock_solver.core.evaluator import evaluate_solution
from crossdock_solver.core.solution import Solution
from crossdock_solver.data.instance import CrossDockInstance
from crossdock_solver.exact.cpsat import ExactCPSATConfig, solve_exact_cpsat


TRUCKS = ["I1", "I2", "I3"]
DESTS = ["D1", "D2", "D3"]
DOORS = [0, 1, 2]
# units per (truck, destination); one product type with unit handling time
UNITS = np.array(
    [
        [4, 8, 3],  # I1
        [8, 4, 0],  # I2
        [3, 8, 0],  # I3: arrives late in the extended setting
    ],
    dtype=float,
)
TRAVEL = np.array([[0, 1, 2], [1, 0, 1], [2, 1, 0]], dtype=float)
ENTER = {t: 1.0 for t in TRUCKS}
LEAVE = {t: 1.0 for t in TRUCKS}
LAMBDA = 1.0
R3 = 15.0
DUE = {"I1": 20.0, "I2": 25.0, "I3": 45.0}


def instance(release: dict[str, float] | None, due: dict[str, float] | None) -> CrossDockInstance:
    return CrossDockInstance(
        compound_trucks=TRUCKS,
        outbound_trucks=[],
        destinations=DESTS,
        doors=DOORS,
        product_types=["K"],
        flow=UNITS[:, :, None],
        product_time=np.array([1.0]),
        travel_time=TRAVEL,
        enter_time=ENTER,
        leave_time=LEAVE,
        release_time=release,
        due_time=due,
    )


def all_solutions():
    for dests in itertools.permutations(DESTS):
        for doors in itertools.permutations(DOORS):
            yield Solution(
                compound_assignment={t: (d, m) for t, d, m in zip(TRUCKS, dests, doors)},
                outbound_assignment={},
                door_sequences={m: [] for m in DOORS},
            )


def score(inst: CrossDockInstance, sol: Solution, weight: float):
    r = evaluate_solution(inst, sol)
    return r.makespan + weight * r.total_tardiness, r


def best(inst: CrossDockInstance, weight: float):
    scored = [(score(inst, s, weight), s) for s in all_solutions()]
    (obj, res), sol = min(scored, key=lambda x: (x[0][0], str(x[1].compound_assignment)))
    return obj, res, sol, scored


def retained(sol: Solution) -> str:
    return ", ".join(f"{t}->{sol.compound_assignment[t][0]}" for t in TRUCKS)


def waits_for(sol: Solution) -> str:
    """For every carrier, the other trucks whose unloaded freight it must wait for."""

    parts = []
    for t in TRUCKS:
        d = DESTS.index(sol.compound_assignment[t][0])
        src = [u for i, u in enumerate(TRUCKS) if u != t and UNITS[i, d] > 0]
        parts.append(f"{t}<-{'+'.join(src) if src else 'none'}")
    return ", ".join(parts)


def late_dependents(sol: Solution, late: str = "I3") -> str:
    """Carriers that wait for the late truck's freight, and how many units."""

    i = TRUCKS.index(late)
    out = []
    for t in TRUCKS:
        if t == late:
            continue
        d = DESTS.index(sol.compound_assignment[t][0])
        if UNITS[i, d] > 0:
            out.append(f"{t}({UNITS[i, d]:g})")
    return ", ".join(out) if out else "none"


def finishes(res) -> str:
    return ", ".join(f"{t} {res.truck_finish[t]:g}" for t in TRUCKS)


def main() -> None:
    base = instance(None, None)
    ext = instance({"I1": 0.0, "I2": 0.0, "I3": R3}, DUE)

    b_obj, b_res, b_sol, b_all = best(base, 0.0)
    e_obj, e_res, e_sol, e_all = best(ext, LAMBDA)
    x_obj, x_res = score(ext, b_sol, LAMBDA)  # base plan under extended data

    for name, inst, weight, obj in (("base", base, 0.0, b_obj), ("extended", ext, LAMBDA, e_obj)):
        cp = solve_exact_cpsat(inst, ExactCPSATConfig(time_limit_sec=60, workers=4, tardiness_weight=weight))
        print(f"CP-SAT check {name}: status={cp.status} objective={cp.objective_value:g} enumeration={obj:g}")
        assert cp.proven_optimal and abs(cp.objective_value - obj) < 1e-6

    print()
    print(f"instance: units (D1,D2,D3) I1={UNITS[0].tolist()} I2={UNITS[1].tolist()} I3={UNITS[2].tolist()}, "
          f"enter=leave=1, travel=|door difference|, lambda={LAMBDA:g}")
    print(f"extended: release I1=0 I2=0 I3={R3:g}; due {DUE}")
    print()
    rows = [
        ("arrival (r_I1, r_I2, r_I3)", "0, 0, 0", f"0, 0, {R3:g}", f"0, 0, {R3:g}"),
        ("soft due (I1, I2, I3)", "none", ", ".join(f"{DUE[t]:g}" for t in TRUCKS), ", ".join(f"{DUE[t]:g}" for t in TRUCKS)),
        ("retained destination", retained(b_sol), retained(b_sol), retained(e_sol)),
        ("carrier waits for freight of", waits_for(b_sol), waits_for(b_sol), waits_for(e_sol)),
        ("carriers waiting on I3 (units)", late_dependents(b_sol), late_dependents(b_sol), late_dependents(e_sol)),
        ("finish (I1, I2, I3)", finishes(b_res), finishes(x_res), finishes(e_res)),
        ("makespan", f"{b_res.makespan:g}", f"{x_res.makespan:g}", f"{e_res.makespan:g}"),
        ("total tardiness", "n/a", f"{x_res.total_tardiness:g}", f"{e_res.total_tardiness:g}"),
        ("J = makespan + lambda*tardiness", f"{b_obj:g}", f"{x_obj:g}", f"{e_obj:g}"),
    ]
    head = ("", "base optimum", "base plan, extended data", "extended optimum")
    widths = [max(len(r[i]) for r in [head, *rows]) for i in range(4)]
    for r in [head, *rows]:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)))
    print()
    print(f"distinct retained-destination patterns among optima: base {retained(b_sol)} | extended {retained(e_sol)}")
    print(f"cost of planning with the base model: J {x_obj:g} vs {e_obj:g} (+{100 * (x_obj / e_obj - 1):.1f}%)")

    print()
    print()
    print("decomposition: which extension changes the optimal retained destinations")
    for label, rel, due, w in (
        ("release only (no due, makespan)", {"I1": 0.0, "I2": 0.0, "I3": R3}, None, 0.0),
        ("due only (r = 0)", None, DUE, LAMBDA),
        ("release + due", {"I1": 0.0, "I2": 0.0, "I3": R3}, DUE, LAMBDA),
    ):
        inst = instance(rel, due)
        opt, pats, _ = optimal_patterns(inst, w)
        kept, _ = score(inst, b_sol, w)
        print(f"  {label:34} optimum J {opt:5g} retained {' | '.join(sorted(pats)):26} "
              f"base plan J {kept:5g} (+{100 * (kept / opt - 1):.1f}%)")

    for label, plan in (("base-optimal plan", b_sol), ("extended-optimal plan", e_sol)):
        propagation(label, plan)

    print()
    print("re-optimized at each R3 (enumeration): retained destinations and J")
    for r3 in range(0, 45, 5):
        inst = instance({"I1": 0.0, "I2": 0.0, "I3": float(r3)}, DUE)
        obj, res, sol, _ = best(inst, LAMBDA)
        print(f"{r3:4d}  {retained(sol):30}  makespan {res.makespan:5g}  tardiness {res.total_tardiness:5g}  J {obj:5g}")

    robustness()


def optimal_patterns(inst: CrossDockInstance, weight: float) -> tuple[float, set[str], list]:
    scored = [(score(inst, s, weight)[0], s) for s in all_solutions()]
    opt = min(o for o, _ in scored)
    return opt, {retained(s) for o, s in scored if abs(o - opt) < 1e-9}, scored


def robustness(samples: int = 1000, seed: int = 2026) -> None:
    """Random 3-truck instances: units U{1..8} on D1, D2, I1 also carries 0-3 units for D3;
    I3 arrives at R3 in {10, 15, 20}; due dates I1, I2 in {20, 25, 30}, I3 = R3 + {20, 25, 30}."""

    global UNITS
    saved = UNITS
    rng = np.random.default_rng(seed)
    flips, excess = 0, []
    for _ in range(samples):
        units = np.zeros((3, 3))
        units[:, :2] = rng.integers(1, 9, size=(3, 2))
        units[0, 2] = rng.integers(1, 4)
        UNITS = units
        r3 = float(rng.choice([10, 15, 20]))
        due = {"I1": float(rng.choice([20, 25, 30])), "I2": float(rng.choice([20, 25, 30])),
               "I3": r3 + float(rng.choice([20, 25, 30]))}
        _, base_pats, _ = optimal_patterns(instance(None, None), 0.0)
        ext_opt, ext_pats, ext_scored = optimal_patterns(instance({"I1": 0.0, "I2": 0.0, "I3": r3}, due), LAMBDA)
        if not base_pats & ext_pats:
            flips += 1
            # best the planner can do while keeping a base-optimal retention pattern
            kept = min(o for o, s in ext_scored if retained(s) in base_pats)
            excess.append(100 * (kept / ext_opt - 1))
    UNITS = saved
    print()
    print(f"robustness ({samples} random instances, seed {seed}): base-optimal retained destinations not optimal "
          f"in the extended setting in {flips} ({100 * flips / samples:.1f}%)")
    if excess:
        excess.sort()
        print(f"  extended J when forced to keep a base-optimal retention pattern: mean +{np.mean(excess):.1f}%, "
              f"median +{np.median(excess):.1f}%, max +{max(excess):.1f}%")


def propagation(label: str, plan: Solution) -> None:
    print()
    print(f"delay propagation, {label} ({retained(plan)}) fixed, R3 varies, due dates as above")
    print(f"{'R3':>4} {'unload end I3':>14} {'D ready':>22} {'finish I1':>10} {'finish I2':>10} {'finish I3':>10}"
          f" {'tardy I1':>9} {'tardy I2':>9} {'tardy I3':>9} {'total':>6} {'makespan':>9}")
    for r3 in range(0, 45, 5):
        inst = instance({"I1": 0.0, "I2": 0.0, "I3": float(r3)}, DUE)
        res = evaluate_solution(inst, plan)
        ready = res.metadata["destination_ready"]
        tardy = {t: max(0.0, res.truck_finish[t] - DUE[t]) for t in TRUCKS}
        print(f"{r3:4d} {res.metadata['compound_unload_finish']['I3']:14g} "
              f"{', '.join(f'{d} {ready[d]:g}' for d in DESTS):>22} "
              + " ".join(f"{res.truck_finish[t]:10g}" for t in TRUCKS) + " "
              + " ".join(f"{tardy[t]:9g}" for t in TRUCKS) + f" {res.total_tardiness:6g} {res.makespan:9g}")



if __name__ == "__main__":
    main()
