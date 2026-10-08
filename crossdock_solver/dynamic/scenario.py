"""Arrival-uncertainty scenarios for the dynamic (online) variant.

A dynamic scenario is a static benchmark instance whose release times are
reinterpreted as *planned* arrivals p_q. The contractual due dates stay as in
the static instance (p_q + delta * H). The realized arrival is

    r_q = max(0, p_q + N(0, (sigma * H)^2) + B_q * Exp(mean = late_mean * H)),
    B_q ~ Bernoulli(late_prob),

i.e. small symmetric noise plus an occasional heavy late tail, scaled by the
same unconstrained-makespan estimate H the generator uses for time windows.

Optionally the compound-truck manifests are uncertain as well: the planned
flow is the pre-advised manifest, and the realized flow of truck i is revealed
only when truck i arrives. Everything else is known at time 0.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import random

import numpy as np

from crossdock_solver.data.generator import _makespan_estimate
from crossdock_solver.data.instance import CrossDockInstance, TruckId


@dataclass(frozen=True)
class ArrivalNoise:
    """Parametric arrival-delay model, expressed as fractions of the horizon H."""

    sigma: float
    late_prob: float
    late_mean: float

    def sample(self, rng: random.Random, planned: float, horizon: float) -> float:
        delay = rng.gauss(0.0, self.sigma * horizon)
        if self.late_mean > 0 and rng.random() < self.late_prob:
            delay += rng.expovariate(1.0 / (self.late_mean * horizon))
        return round(max(0.0, planned + delay), 1)

    def sample_after(
        self,
        rng: random.Random,
        planned: float,
        horizon: float,
        after: float,
        *,
        max_tries: int = 200,
    ) -> float:
        """Sample an arrival conditioned on the truck not having arrived by `after`.

        Rejection sampling from the unconditional model; if the condition is far
        in the tail, fall back to `after` plus a memoryless late delay.
        """

        for _ in range(max_tries):
            arrival = self.sample(rng, planned, horizon)
            if arrival > after:
                return arrival
        tail_mean = max(self.late_mean, self.sigma, 1e-3) * horizon
        return round(after + 0.1 + rng.expovariate(1.0 / tail_mean), 1)


UNCERTAINTY_LEVELS: dict[str, ArrivalNoise] = {
    "low": ArrivalNoise(sigma=0.02, late_prob=0.10, late_mean=0.05),
    "medium": ArrivalNoise(sigma=0.05, late_prob=0.20, late_mean=0.10),
    "high": ArrivalNoise(sigma=0.08, late_prob=0.30, late_mean=0.20),
}


@dataclass(frozen=True)
class ManifestNoise:
    """Pre-advised vs actual cargo: each (truck, destination, product) entry is
    redrawn from U[0, flow_high] with probability `redraw_prob`, otherwise
    scaled by U[1 - scale, 1 + scale] and rounded."""

    redraw_prob: float
    scale: float = 0.2
    flow_high: int = 20

    def sample(self, rng: np.random.Generator, planned_flow: np.ndarray) -> np.ndarray:
        shape = planned_flow.shape
        perturbed = np.rint(planned_flow * rng.uniform(1 - self.scale, 1 + self.scale, shape))
        fresh = rng.integers(0, self.flow_high + 1, shape)
        redraw = rng.random(shape) < self.redraw_prob
        return np.where(redraw, fresh, perturbed).astype(float)


MANIFEST_LEVELS: dict[str, ManifestNoise] = {
    "low": ManifestNoise(redraw_prob=0.10),
    "medium": ManifestNoise(redraw_prob=0.25),
    "high": ManifestNoise(redraw_prob=0.50),
}


@dataclass(frozen=True)
class DynamicScenario:
    """A planned instance plus one realization of arrivals (and manifests)."""

    planned: CrossDockInstance
    arrival: dict[TruckId, float]
    noise: ArrivalNoise
    horizon: float
    flow: np.ndarray | None = None
    manifest_noise: ManifestNoise | None = None

    @property
    def realized_flow(self) -> np.ndarray:
        return self.planned.flow if self.flow is None else self.flow

    def realized_instance(self) -> CrossDockInstance:
        return replace(
            self.planned,
            release_time=dict(self.arrival),
            flow=self.realized_flow.copy(),
        )

    def arrival_order(self) -> list[TruckId]:
        """Decision order: realized arrival time, ties broken by truck order."""

        order = {truck: idx for idx, truck in enumerate(self.planned.all_trucks)}
        return sorted(self.planned.all_trucks, key=lambda t: (self.arrival[t], order[t]))


def horizon_of(instance: CrossDockInstance) -> float:
    return _makespan_estimate(instance.flow, instance.product_time, len(instance.doors))


def make_scenario(
    planned: CrossDockInstance,
    noise: ArrivalNoise | str,
    *,
    seed: int,
    manifest: ManifestNoise | str | None = None,
) -> DynamicScenario:
    noise = _level(noise, UNCERTAINTY_LEVELS, "uncertainty")
    rng = random.Random(seed)
    horizon = horizon_of(planned)
    arrival = {
        truck: noise.sample(rng, planned.release_time[truck], horizon)
        for truck in planned.all_trucks
    }
    flow = None
    if manifest is not None:
        manifest = _level(manifest, MANIFEST_LEVELS, "manifest")
        flow = manifest.sample(np.random.default_rng(seed + 7_919), planned.flow)
    return DynamicScenario(
        planned=planned,
        arrival=arrival,
        noise=noise,
        horizon=horizon,
        flow=flow,
        manifest_noise=manifest,
    )


def _level(value, levels: dict, label: str):
    if not isinstance(value, str):
        return value
    if value not in levels:
        raise ValueError(f"{label} level must be one of {tuple(levels)}, got {value!r}")
    return levels[value]
