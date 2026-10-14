"""Lower bound on the long-run objective J of a stream (policy independent).

Relaxation: no yard wait, no door contention, and every truck may act as the
carrier of *every* destination at once (a carrier normally serves one). The
arrival sequence of a stream does not depend on the policy, so the bound is
valid for every policy run on the same seed.

For a measured compound truck i (arrival a_i) that retains destination r, with
unloading done at u_i = a_i + enter_i + handling(all but r):

- retained units leave with the truck:            lead >= u_i + leave_i - a_i
- a lot for destination d != r is ready at u_i and needs another truck j as
  carrier. j can claim it only if j's loading phase starts after i docked:
  c_j(d) = a_j + enter_j (+ handling(all but d) if j is a compound truck) >= a_i.
  The lot then reaches j's door no earlier than u_i + min_travel, is loaded
  (at least its own handling) and leaves with j:
      lead >= min_j [ max(c_j(d), u_i + min_travel) + handling_i(d) + leave_j ] - a_i
- tardiness of i >= max(0, u_i + leave_i - due_i)

Outbound trucks carry no measured freight; their tardiness bound is
max(0, a + enter + leave - due) (zero in practice). For every truck the
retention r with the smallest contribution to
J = sum(units * lead) / units + lambda * sum(tardiness) / trucks is taken.

The "carrier" term captures the wait for the next truck that can carry a
destination, which dominates lead time at low load; congestion is ignored, so
the bound loosens as the load grows.
"""

from __future__ import annotations

import numpy as np

from crossdock_solver.stream.sim import CrossDockStream


def stream_lower_bound(env: CrossDockStream) -> float:
    """Lower bound on `env.metrics().objective`. Call after the stream was run
    by any policy (so that every truck needed as a potential carrier exists)."""

    measured = env._measured
    if not measured:
        return 0.0
    fac = env.facility
    travel = fac.travel
    off = travel[~np.eye(len(travel), dtype=bool)]
    min_travel = float(off.min()) if off.size else 0.0
    weight = env.config.tardiness_weight

    trucks = sorted({id(t): t for t in [*env.departed, *env.in_system]}.values(), key=lambda t: t.uid)
    arrival = np.array([t.arrival for t in trucks])
    enter = np.array([t.enter for t in trucks])
    leave = np.array([t.leave for t in trucks])
    handling = np.array([t.handling for t in trucks])  # (N, D)
    compound = np.array([t.compound for t in trucks])
    total = handling.sum(axis=1)
    claim = arrival[:, None] + enter[:, None] + np.where(compound[:, None], total[:, None] - handling, 0.0)
    index = {t.uid: k for k, t in enumerate(trucks)}

    total_units = sum(float(t.units.sum()) for t in measured if t.compound)
    lead_sum = 0.0
    tard_sum = 0.0
    n = len(measured)
    for truck in measured:
        if not truck.compound:
            tard_sum += max(0.0, truck.arrival + truck.enter + truck.leave - truck.due)
            continue
        k = index[truck.uid]
        a = truck.arrival
        valid = claim >= a  # (N, D)
        valid[k] = False
        D = len(truck.units)
        best_value, best_lead, best_tard = np.inf, 0.0, 0.0
        for r in range(D):
            done = a + truck.enter + total[k] - truck.handling[r]
            lead = truck.units[r] * (done + truck.leave - a)
            ready = done + min_travel
            depart = np.where(valid, np.maximum(claim, ready) + leave[:, None], np.inf).min(axis=0)  # (D,)
            depart = np.where(np.isfinite(depart), depart, ready + 1.0)  # no later truck recorded
            for d in range(D):
                if d != r and truck.units[d] > 0:
                    lead += truck.units[d] * (depart[d] + truck.handling[d] - a)
            tard = max(0.0, done + truck.leave - truck.due)
            value = lead / total_units + weight * tard / n
            if value < best_value:
                best_value, best_lead, best_tard = value, lead, tard
        lead_sum += best_lead
        tard_sum += best_tard
    return lead_sum / total_units + weight * tard_sum / n
