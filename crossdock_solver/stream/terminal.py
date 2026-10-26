"""Learned terminal delay for the rolling-horizon model (optimization-augmented policy).

The rolling CP-SAT model (rolling.py) only knows the trucks at hand. Freight
none of them can carry goes to the terminal sweeper, which claims at the
model's last departure Cmax plus a delay W_d. With one tuned constant the
policy is very sensitive to W (5.6). Here a small network predicts W_d from the
state, per destination: the expected time between Cmax and the claim of the
next carrier of d that is not in the model (a yard truck beyond the first
`max_yard` or a future arrival). It is a predict-then-optimize layer: the
network supplies the parameter, CP-SAT makes the decision.

Labels come from reference trajectories (any policy) on TRAIN streams: at each
decision, Cmax is approximated by the realized last departure of the trucks the
model would include, and the label is the realized wait until the next
out-of-model carrier of d claims.
"""

from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn

from crossdock_solver.stream.policies import backlog_handling
from crossdock_solver.stream.sim import CrossDockStream

NUM_TERMINAL_FEATURES = 14


def terminal_features(env: CrossDockStream, max_yard: int) -> np.ndarray:
    """(D, F) features, times and handling in units of the mean truck work."""

    fac = env.facility
    cfg = env.config
    D, doors, work = cfg.num_destinations, cfg.num_doors, fac.mean_work
    now = env.now
    backlog = backlog_handling(env) / work
    unready = np.zeros(D)
    oldest = np.zeros(D)
    for d, lots in enumerate(env.open_lots):
        if lots:
            unready[d] = sum(lot.handling for lot in lots if lot.ready > now) / work
            oldest[d] = (now - min(lot.source.arrival for lot in lots)) / work
    since_last = (now - env.last_departure) / work
    beyond = env.yard[max_yard:]
    compounds_beyond = np.zeros(D)
    for truck in beyond:
        if truck.compound:
            compounds_beyond[int(np.argmax(truck.handling))] += 1
    outbound_beyond = sum(not t.compound for t in beyond)
    docked = [t for t in env.doors if t is not None]
    open_carriers = np.zeros(D)
    for truck in docked:
        if math.isnan(truck.claim_time):
            open_carriers[truck.destination] += 1
    out = np.zeros((D, NUM_TERMINAL_FEATURES), dtype=np.float32)
    out[:, 0] = backlog
    out[:, 1] = unready
    out[:, 2] = oldest
    out[:, 3] = np.minimum(since_last, 20.0)
    out[:, 4] = fac.demand_weight / D
    out[:, 5] = len(env.yard) / doors
    out[:, 6] = len(beyond) / doors
    out[:, 7] = compounds_beyond / doors
    out[:, 8] = outbound_beyond / doors
    out[:, 9] = fac.arrival_rate * work / doors  # load
    out[:, 10] = D / doors
    out[:, 11] = 1.0 / D
    out[:, 12] = len(docked) / doors
    out[:, 13] = open_carriers
    return out


class TerminalNet(nn.Module):
    """W_d / mean_work = softplus(MLP(features_d))."""

    def __init__(self, hidden: int = 32) -> None:
        super().__init__()
        self.body = nn.Sequential(nn.Linear(NUM_TERMINAL_FEATURES, hidden), nn.ReLU(),
                                  nn.Linear(hidden, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return nn.functional.softplus(self.body(x)).squeeze(-1)


class LearnedTerminal:
    """callable(env, max_yard) -> per-destination delays in time units."""

    def __init__(self, net: TerminalNet, scale: float = 1.0) -> None:
        self.net = net.eval()
        self.scale = scale

    @torch.no_grad()
    def __call__(self, env: CrossDockStream, max_yard: int) -> list[float]:
        x = torch.from_numpy(terminal_features(env, max_yard))
        return (self.scale * env.facility.mean_work * self.net(x)).tolist()


def collect_terminal_labels(env: CrossDockStream, policy, max_yard: int = 8) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Run `policy` on `env`; return (features (D, F), label (D,), valid (D,)) per decision.

    label_d = (claim time of the next carrier of d outside the model) - (realized
    last departure of the trucks inside the model), clipped at 0, in units of the
    mean truck work; valid is False when no such carrier was observed."""

    if hasattr(policy, "reset"):
        policy.reset(env)
    states = []
    while not env.done:
        included = [t for t in env.doors if t is not None] + env.yard[:max_yard]
        states.append((terminal_features(env, max_yard), [t for t in included], {t.uid for t in included}, env.now))
        action = policy.act(env)
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)
    trucks = [t for t in [*env.departed, *env.in_system] if not math.isnan(t.claim_time)]
    D = env.config.num_destinations
    claims = [sorted((t.claim_time, t.uid) for t in trucks if t.destination == d) for d in range(D)]
    work = env.facility.mean_work
    out = []
    for feats, included, ids, now in states:
        ends = [t.departure for t in included]
        if any(math.isnan(x) for x in ends):
            continue  # the run ended before these trucks left (time cap)
        cmax = max(ends) if ends else now
        label = np.zeros(D, dtype=np.float32)
        valid = np.zeros(D, dtype=bool)
        for d in range(D):
            for claim, uid in claims[d]:
                if claim >= now and uid not in ids:
                    label[d] = max(0.0, claim - cmax) / work
                    valid[d] = True
                    break
        out.append((feats, label, valid))
    return out


def fit_terminal(net: TerminalNet, data, *, epochs: int = 40, lr: float = 1e-3, seed: int = 0) -> float:
    """Huber regression on the valid (state, destination) labels."""

    feats = np.concatenate([f[v] for f, _, v in data])
    labels = np.concatenate([y[v] for _, y, v in data])
    x, y = torch.from_numpy(feats), torch.from_numpy(labels)
    gen = torch.Generator().manual_seed(seed)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    loss_value = float("nan")
    for _ in range(epochs):
        order = torch.randperm(len(y), generator=gen)
        for start in range(0, len(y), 512):
            idx = order[start : start + 512]
            loss = nn.functional.huber_loss(net(x[idx]), y[idx], delta=1.0)
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_value = float(loss)
    return loss_value
