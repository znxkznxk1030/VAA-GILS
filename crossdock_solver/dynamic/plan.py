"""Committed decisions, forecast instances and plan projection.

Decision protocol (v1): when truck q arrives it is irrevocably assigned a
destination and a door. A compound truck takes a door no other compound truck
holds (|I| = |M|, so every door ends up with exactly one compound truck); an
outbound truck is appended to the end of its door's outbound queue. Because
outbound trucks never start before the compound truck of their door finishes,
evaluating the final assignment with the static evaluator on the realized
instance reproduces exactly the schedule that unfolds online.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

import numpy as np

from crossdock_solver.core.solution import Solution
from crossdock_solver.data.instance import CrossDockInstance, DestinationId, DoorId, TruckId


@dataclass(frozen=True)
class Decision:
    truck: TruckId
    destination: DestinationId
    door: DoorId


def tardiness_weight(instance: CrossDockInstance) -> float:
    """lambda = 1 when any due date is finite, as in the static experiments."""

    return 1.0 if any(d != float("inf") for d in instance.due_time.values()) else 0.0


def forecast_instance(
    planned: CrossDockInstance,
    time: float,
    arrived: Mapping[TruckId, float],
    manifests: Mapping[TruckId, np.ndarray] | None = None,
) -> CrossDockInstance:
    """Certainty-equivalent instance at `time`.

    Arrived trucks keep their realized arrival; a truck not yet arrived is
    assumed to arrive at its planned time, or right now if it is already late.
    Revealed manifests replace the pre-advised flow rows of their trucks.
    """

    release = {
        truck: arrived[truck] if truck in arrived else max(planned.release_time[truck], time)
        for truck in planned.all_trucks
    }
    if not manifests:
        return replace(planned, release_time=release)
    flow = planned.flow.copy()
    for truck, row in manifests.items():
        flow[planned.compound_index[truck]] = row
    return replace(planned, release_time=release, flow=flow)


def project(
    instance: CrossDockInstance,
    solution: Solution,
    commitments: Sequence[Decision],
) -> Solution:
    """Smallest repair of `solution` that honours every committed decision.

    Commitments are applied in commit order. A destination (or compound door)
    already held by another truck is swapped with that truck; by induction the
    other truck is never a committed one, because committed decisions use
    distinct destinations and distinct compound doors. On each door the
    committed outbound trucks form a prefix in commit order, followed by the
    uncommitted ones in their original order.
    """

    plan = solution.copy()
    compounds = plan.compound_assignment
    outbounds = plan.outbound_assignment
    carrier = plan.destination_carriers()
    compound_on_door = {door: truck for truck, (_, door) in compounds.items()}
    committed_prefix: dict[DoorId, list[TruckId]] = {}
    committed: set[TruckId] = set()

    for decision in commitments:
        truck = decision.truck
        committed.add(truck)
        current = plan.truck_destination(truck)
        if current != decision.destination:
            holder = carrier[decision.destination]
            _set_destination(plan, holder, current)
            _set_destination(plan, truck, decision.destination)
            carrier[current] = holder
            carrier[decision.destination] = truck

        if truck in compounds:
            destination, door = compounds[truck]
            if door != decision.door:
                other = compound_on_door.get(decision.door)
                if other is not None:
                    compounds[other] = (compounds[other][0], door)
                    compound_on_door[door] = other
                else:
                    del compound_on_door[door]
                compounds[truck] = (destination, decision.door)
                compound_on_door[decision.door] = truck
        else:
            outbounds[truck] = (outbounds[truck][0], decision.door)
            committed_prefix.setdefault(decision.door, []).append(truck)

    if committed_prefix:
        for door in instance.doors:
            rest = [t for t in plan.door_sequences.get(door, []) if t not in committed]
            plan.door_sequences[door] = [*committed_prefix.get(door, []), *rest]
    return plan


def assignment_of(solution: Solution, truck: TruckId) -> tuple[DestinationId, DoorId]:
    if truck in solution.compound_assignment:
        return solution.compound_assignment[truck]
    return solution.outbound_assignment[truck]


def _set_destination(solution: Solution, truck: TruckId, destination: DestinationId) -> None:
    if truck in solution.compound_assignment:
        solution.compound_assignment[truck] = (destination, solution.compound_assignment[truck][1])
    else:
        solution.outbound_assignment[truck] = (destination, solution.outbound_assignment[truck][1])
