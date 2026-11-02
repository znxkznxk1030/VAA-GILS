"""Time-varying destination demand and the forecasts a policy may hold (C3 gate).

The real stream draws arrivals from `TrueDemand`, a non-homogeneous Poisson
process (thinning) whose total rate and destination shares follow sine waves:

    rate(t)  = rate_bar * (1 + A   * sin(2 pi t / P + phase_0))
    w_d(t)  ~= w_d      * (1 + A_d * sin(2 pi t / P + phase_d)),  sum_d w_d(t) = |D|

With A = A_d = 0 it is the stationary stream of the earlier experiments and
the simulator takes exactly the old random-number path.

A look-ahead fork samples its future arrivals from a demand model. Which
model it is defines the information level of the C3 design:

    I0  StationaryDemand : long-run averages only (rate_bar, w_d)
    I1  NoisyDemand      : true curves times a log-normal AR(1) error
    I2  TrueDemand       : the true curves (distribution known, realization not)
    I3  fork(oracle=True): the real future (value of information only)
"""

from __future__ import annotations

import math

import numpy as np

from crossdock_solver.stream.config import Facility


class DemandModel:
    """Arrival rate and destination shares as functions of time."""

    stationary: bool = False

    def __init__(self, facility: Facility) -> None:
        self.facility = facility

    def rate(self, t: float) -> float:
        raise NotImplementedError

    def weights(self, t: float) -> np.ndarray:
        raise NotImplementedError

    @property
    def rate_max(self) -> float:
        raise NotImplementedError

    def expected_units(self, t0: float, t1: float, points: int = 17) -> np.ndarray:
        """Expected freight units per destination brought by trucks arriving in
        [t0, t1] (trapezoid rule). Policy-visible forecast quantity."""

        if t1 <= t0:
            return np.zeros(self.facility.num_destinations)
        cfg = self.facility.config
        grid = np.linspace(t0, t1, points)
        values = np.array([
            self.rate(t) * cfg.compound_fraction * cfg.num_products
            * np.floor(cfg.flow_high * self.weights(t)) / 2.0
            for t in grid
        ])
        return np.trapezoid(values, grid, axis=0)


class StationaryDemand(DemandModel):
    """I0: the long-run averages, i.e. the stream of the earlier experiments."""

    stationary = True

    def rate(self, t: float) -> float:
        return self.facility.arrival_rate

    def weights(self, t: float) -> np.ndarray:
        return self.facility.demand_weight

    @property
    def rate_max(self) -> float:
        return self.facility.arrival_rate


class TrueDemand(DemandModel):
    """I2 and the real stream: sine-wave rate and destination shares."""

    def __init__(self, facility: Facility) -> None:
        super().__init__(facility)
        cfg = facility.config
        self.amplitude = cfg.amplitude
        self.dest_amplitude = cfg.dest_amplitude
        self.period = cfg.period_sla * facility.sla
        self.stationary = self.amplitude == 0 and self.dest_amplitude == 0

    def _wave(self, t: float, phase) -> np.ndarray | float:
        return np.sin(2.0 * math.pi * t / self.period + phase)

    def rate(self, t: float) -> float:
        if self.amplitude == 0:
            return self.facility.arrival_rate
        return self.facility.arrival_rate * (1.0 + self.amplitude * float(self._wave(t, self.facility.phase[0])))

    def weights(self, t: float) -> np.ndarray:
        base = self.facility.demand_weight
        if self.dest_amplitude == 0:
            return base
        w = base * (1.0 + self.dest_amplitude * self._wave(t, self.facility.phase[1:]))
        return w * len(w) / w.sum()

    @property
    def rate_max(self) -> float:
        return self.facility.arrival_rate * (1.0 + self.amplitude)


class NoisyDemand(DemandModel):
    """I1: the true curves times exp(sigma * e(t) - sigma^2 / 2), where e is a
    unit-variance AR(1) series per curve (rate + each destination) on a grid of
    one mean truck work, linearly interpolated. The error is fixed per stream
    (`seed`), i.e. a property of the forecast, not redrawn per look-ahead."""

    def __init__(self, true: TrueDemand, sigma: float, seed: int, *, rho: float = 0.9,
                 phase_error: float = 0.0) -> None:
        super().__init__(true.facility)
        self.true = true
        self.sigma = sigma
        self.phase_error = phase_error  # radians added to every wave (biased timing)
        self.step = true.facility.mean_work
        self._rng = np.random.default_rng(seed)
        self.rho = rho
        self._series = np.zeros((0, true.facility.num_destinations + 1))

    def _noise(self, t: float) -> np.ndarray:
        k = max(0.0, t) / self.step
        need = int(k) + 2
        if len(self._series) < need:
            series = list(self._series)
            width = self._series.shape[1]
            scale = math.sqrt(1.0 - self.rho ** 2)
            while len(series) < need:
                shock = self._rng.standard_normal(width)
                series.append(shock if not series else self.rho * series[-1] + scale * shock)
            self._series = np.array(series)
        i = int(k)
        frac = k - i
        e = (1.0 - frac) * self._series[i] + frac * self._series[i + 1]
        return np.exp(self.sigma * e - 0.5 * self.sigma ** 2)

    def _shifted(self, t: float) -> float:
        return t + self.phase_error * self.true.period / (2.0 * math.pi)

    def rate(self, t: float) -> float:
        return self.true.rate(self._shifted(t)) * float(self._noise(t)[0])

    def weights(self, t: float) -> np.ndarray:
        w = self.true.weights(self._shifted(t)) * self._noise(t)[1:]
        return w * len(w) / w.sum()

    @property
    def rate_max(self) -> float:
        # thinning bound; the simulator caps rate(t) here (noise factor <= exp(4 sigma))
        return self.true.rate_max * math.exp(4.0 * self.sigma)


def demand_model(level: str, facility: Facility, *, sigma: float = 0.2, seed: int = 0) -> DemandModel:
    """Model for information level "I0", "I1" or "I2" (I3 is `fork(oracle=True)`)."""

    true = TrueDemand(facility)
    if level == "I0":
        return StationaryDemand(facility)
    if level == "I1":
        return NoisyDemand(true, sigma, seed)
    if level == "I2":
        return true
    raise ValueError(f"unknown information level {level!r}")
