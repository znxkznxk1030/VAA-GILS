"""Facility and arrival-stream configuration for the continuous cross-dock.

The static model has exactly one carrier per destination (|I| + |F| = |D|)
and one closed batch of trucks. The stream variant keeps the compound-truck
mechanics but lets trucks arrive without end, so over time |I| + |F| >> |D|:
every destination is served by many carriers and freight waiting for a
destination is consolidated on whichever carrier serves it next.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


DEMAND_PATTERNS = ("uniform", "skewed")


@dataclass(frozen=True)
class StreamConfig:
    num_doors: int
    num_destinations: int
    num_products: int = 3
    compound_fraction: float = 2 / 3
    load: float = 0.85
    sla_factor: float = 3.0
    demand: str = "uniform"
    flow_high: int = 20
    tardiness_weight: float = 1.0

    def __post_init__(self) -> None:
        if self.num_destinations > self.num_doors:
            raise ValueError("num_destinations must not exceed num_doors")
        if self.demand not in DEMAND_PATTERNS:
            raise ValueError(f"demand must be one of {DEMAND_PATTERNS}, got {self.demand!r}")
        if not 0 < self.load < 1.2:
            raise ValueError("load must be in (0, 1.2)")


SIZE_PRESETS: dict[str, tuple[int, int]] = {
    # (doors, destinations)
    "S": (6, 4),
    "M": (10, 6),
    "L": (16, 8),
}


def stream_config(size: str, *, load: float = 0.85, demand: str = "uniform", **kwargs) -> StreamConfig:
    doors, destinations = SIZE_PRESETS[size]
    return StreamConfig(
        num_doors=doors,
        num_destinations=destinations,
        load=load,
        demand=demand,
        **kwargs,
    )


@dataclass(frozen=True)
class Facility:
    """Static data of one stream: door layout, handling times, demand shares."""

    config: StreamConfig
    travel: np.ndarray
    product_time: np.ndarray
    demand_weight: np.ndarray
    arrival_rate: float
    mean_work: float
    mean_units: float

    @property
    def num_doors(self) -> int:
        return self.config.num_doors

    @property
    def num_destinations(self) -> int:
        return self.config.num_destinations

    @property
    def sla(self) -> float:
        return self.config.sla_factor * self.mean_work


def build_facility(config: StreamConfig, rng: np.random.Generator) -> Facility:
    doors = config.num_doors
    coordinates = rng.uniform(0, 100, size=(doors, 2))
    diff = coordinates[:, None, :] - coordinates[None, :, :]
    travel = np.round(np.linalg.norm(diff, axis=2) / 10, 2)
    product_time = rng.integers(1, 5, size=config.num_products).astype(float)

    if config.demand == "uniform":
        weight = np.ones(config.num_destinations)
    else:
        weight = 1.0 / np.arange(1, config.num_destinations + 1)
        weight = weight * config.num_destinations / weight.sum()
        weight = weight[rng.permutation(config.num_destinations)]

    # Expected units per (destination, product): U[0, flow_high * weight] has mean
    # flow_high * weight / 2.
    unit_mean = config.flow_high * weight / 2.0
    units_per_compound = float(unit_mean.sum() * config.num_products)
    handling_per_compound = float(unit_mean.sum() * product_time.sum())
    enter_leave = 6.0  # E[U{1..5}] * 2
    # Non-retained freight is handled twice (unload at source, load at carrier);
    # roughly 1/|D| of a compound's cargo is retained and never handled.
    retained = 1.0 / config.num_destinations
    compound_work = enter_leave + 2.0 * handling_per_compound * (1.0 - retained)
    outbound_work = enter_leave
    p = config.compound_fraction
    mean_work = p * compound_work + (1 - p) * outbound_work
    arrival_rate = config.load * doors / mean_work
    return Facility(
        config=config,
        travel=travel,
        product_time=product_time,
        demand_weight=weight,
        arrival_rate=arrival_rate,
        mean_work=mean_work,
        mean_units=p * units_per_compound,
    )
