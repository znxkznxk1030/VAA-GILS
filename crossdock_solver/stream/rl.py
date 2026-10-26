"""Reinforcement-learning dispatcher for the continuous cross-dock.

At every decision epoch the candidate set is
    {(truck, door, destination): truck in the first K yard trucks,
     door free, destination in D}  plus  HOLD,
and a shared MLP scores each candidate from size-invariant features (time in
units of the mean truck work, freight in units of the mean truck load). The
same network therefore runs on any number of doors and destinations.

Training: behaviour cloning of the FCFS-VAA rule as a warm start, then PPO
with the dense cost accrual of the simulator as reward and a continuous-time
discount exp(-dt / tau) between decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import time

import numpy as np
import torch
from torch import nn

from crossdock_solver.stream.config import StreamConfig
from crossdock_solver.stream.policies import FCFSRulePolicy
from crossdock_solver.stream.sim import CrossDockStream


NUM_FEATURES = 24
GLOBAL_FEATURES = 14


def global_features(env: CrossDockStream) -> np.ndarray:
    """System-level state for the critic (and the first four for every candidate)."""

    fac = env.facility
    cfg = env.config
    work = fac.mean_work
    unit = max(fac.mean_units, 1.0)
    doors = cfg.num_doors
    now = env.now
    docked = [t for t in env.doors if t is not None]
    pre_claim = sum(math.isnan(t.claim_time) for t in docked)
    remaining = [
        max(0.0, t.expected_departure - now) for t in docked if not math.isnan(t.expected_departure)
    ]
    lots = [lot for group in env.open_lots for lot in group]
    backlog = sum(lot.handling for lot in lots)
    unready = sum(lot.handling for lot in lots if lot.ready > now)
    oldest = max((now - lot.source.arrival for lot in lots), default=0.0)
    waits = [now - t.arrival for t in env.yard]
    compounds = sum(t.compound for t in env.yard)
    return np.array(
        [
            len(env.yard) / doors,
            len(env.free_doors()) / doors,
            env.units_in_system / (unit * doors),
            1.0 / cfg.num_destinations,
            compounds / doors,
            (len(env.yard) - compounds) / doors,
            sum(float(t.units.sum()) for t in env.yard) / (unit * doors),
            backlog / (work * doors),
            unready / (work * doors),
            pre_claim / doors,
            (float(np.mean(remaining)) / work) if remaining else 0.0,
            oldest / work,
            (float(np.mean(waits)) / work) if waits else 0.0,
            (max(waits) / work) if waits else 0.0,
        ]
    )


def candidate_features(env: CrossDockStream):
    """Feature matrix (N + 1, NUM_FEATURES) in `env.candidates()` order, HOLD last,
    and the global state vector."""

    fac = env.facility
    cfg = env.config
    work = fac.mean_work
    unit = max(fac.mean_units, 1.0)
    now = env.now
    D = cfg.num_destinations
    trucks = env.yard[: env.max_candidates]
    doors = env.free_doors()
    T, F = len(trucks), len(doors)
    travel = fac.travel
    mean_travel = max(float(travel.mean()), 1e-6)

    # destination-level state
    backlog_h = np.zeros(D)
    unready_h = np.zeros(D)
    oldest = np.zeros(D)
    src_units = np.zeros((D, cfg.num_doors))
    ready_at = np.full((D, F), -np.inf)
    for d, lots in enumerate(env.open_lots):
        if not lots:
            continue
        for lot in lots:
            backlog_h[d] += lot.handling
            if lot.ready > now:
                unready_h[d] += lot.handling
            src_units[d, lot.door] += lot.units
        oldest[d] = now - min(lot.source.arrival for lot in lots)
        arrival_at = np.array([lot.ready for lot in lots])[:, None] + travel[
            np.array([lot.door for lot in lots])
        ][:, doors]
        ready_at[d] = arrival_at.max(axis=0)
    lot_units = src_units.sum(axis=1)
    transfer = np.where(
        lot_units[:, None] > 0,
        (src_units @ travel[:, doors]) / np.maximum(lot_units[:, None], 1e-9),
        0.0,
    ) / mean_travel  # (D, F)

    pending = np.zeros(D)
    for truck in env.doors:
        if truck is not None and math.isnan(truck.claim_time):
            pending[truck.destination] += 1
    since_last = (now - env.last_departure) / work
    demand = fac.demand_weight / fac.demand_weight.sum()
    incoming = np.zeros(D)
    for truck in env.yard:
        incoming += truck.units
    incoming /= unit
    centrality = travel[:, doors].mean(axis=0) / mean_travel if F else np.zeros(0)

    full_glob = global_features(env)
    glob = full_glob[:4]

    rule = FCFSRulePolicy().act(env) if T and F else None
    feats = np.zeros((T, F, D, NUM_FEATURES))
    for ti, truck in enumerate(trucks):
        total_h = float(truck.handling.sum())
        unload = (total_h - truck.handling) if truck.compound else np.zeros(D)  # (D,)
        claim_time = now + truck.enter + unload  # (D,)
        wait = np.maximum(0.0, ready_at - claim_time[:, None]) / work  # (D, F)
        wait = np.where(np.isfinite(wait), wait, 0.0)
        share = truck.units / max(float(truck.units.sum()), 1.0)
        f = feats[ti]
        f[..., 0] = float(truck.compound)
        f[..., 1] = (now - truck.arrival) / work
        f[..., 2] = (truck.due - now) / work
        f[..., 3] = ti / env.max_candidates
        f[..., 4] = share[None, :]
        f[..., 5] = total_h / work
        f[..., 6] = (unload / work)[None, :]
        f[..., 7] = (backlog_h / work)[None, :]
        f[..., 8] = (oldest / work)[None, :]
        f[..., 9] = (unready_h / work)[None, :]
        f[..., 10] = pending[None, :]
        f[..., 11] = since_last[None, :]
        f[..., 12] = (demand * D)[None, :]
        f[..., 13] = incoming[None, :]
        f[..., 14] = centrality[:, None]
        f[..., 15] = transfer.T
        f[..., 16] = wait.T
        f[..., 17] = (truck.handling / work)[None, :]
        f[..., 18:22] = glob
        f[..., 22] = float(ti == 0)
    if rule is not None:
        r_truck, r_door, r_dest = rule
        feats[0, doors.index(r_door), r_dest, 23] = 1.0
    flat = feats.reshape(T * F * D, NUM_FEATURES)
    hold = np.zeros((1, NUM_FEATURES))
    hold[0, 18:22] = glob
    hold[0, 0] = -1.0  # hold marker
    return np.concatenate([flat, hold]).astype(np.float32), full_glob.astype(np.float32)


def rule_index(env: CrossDockStream) -> int:
    truck, door, destination = FCFSRulePolicy().act(env)
    trucks = env.yard[: env.max_candidates]
    doors = env.free_doors()
    D = env.config.num_destinations
    return (trucks.index(truck) * len(doors) + doors.index(door)) * D + destination


class DispatchNet(nn.Module):
    def __init__(self, hidden: int = 64) -> None:
        super().__init__()
        self.score = nn.Sequential(
            nn.Linear(NUM_FEATURES, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
        )
        self.value = nn.Sequential(
            nn.Linear(GLOBAL_FEATURES + 2 * NUM_FEATURES, hidden),
            nn.Tanh(),
            nn.Linear(hidden, hidden),
            nn.Tanh(),
            nn.Linear(hidden, 1),
        )

    def logits(self, feats: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """feats (B, N, F), mask (B, N) true for real candidates."""

        out = self.score(feats).squeeze(-1)
        return out.masked_fill(~mask, -1e9)

    def values(self, feats: torch.Tensor, mask: torch.Tensor, glob: torch.Tensor) -> torch.Tensor:
        real = mask.clone()
        real[torch.arange(mask.shape[0]), mask.sum(1) - 1] = False  # drop HOLD
        weight = real.float().unsqueeze(-1)
        count = weight.sum(1).clamp(min=1.0)
        mean = (feats * weight).sum(1) / count
        maxed = feats.masked_fill(~real.unsqueeze(-1), -1e9).max(1).values
        maxed = torch.where(real.any(1, keepdim=True), maxed, torch.zeros_like(maxed))
        return self.value(torch.cat([glob, mean, maxed], dim=-1)).squeeze(-1)


class RLPolicy:
    """Greedy (argmax) or sampling dispatcher backed by a `DispatchNet`."""

    def __init__(self, net: DispatchNet, *, sample: bool = False, seed: int = 0, name: str = "RL-PPO") -> None:
        self.net = net
        self.sample = sample
        self.name = name
        self._gen = torch.Generator().manual_seed(seed)

    @torch.no_grad()
    def act(self, env: CrossDockStream):
        feats, _ = candidate_features(env)
        x = torch.from_numpy(feats).unsqueeze(0)
        mask = torch.ones(1, len(feats), dtype=torch.bool)
        logits = self.net.logits(x, mask)[0]
        if self.sample:
            index = int(torch.multinomial(torch.softmax(logits, 0), 1, generator=self._gen))
        else:
            index = int(torch.argmax(logits))
        return decode(env, index)


class LinearScorePolicy:
    """Same information as the network (candidate_features, HOLD included) but a
    linear score w . x. With w = e_23 (the rule-indicator feature) it reproduces
    FCFS-VAA; tuned by experiments/stream_rule_tune.py --kind linear24 as the
    same-information linear baseline."""

    def __init__(self, weights, name: str = "Tuned-Linear") -> None:
        self.weights = np.asarray(weights, dtype=np.float32)
        if self.weights.shape != (NUM_FEATURES,):
            raise ValueError(f"need {NUM_FEATURES} weights")
        self.name = name

    def act(self, env: CrossDockStream):
        feats, _ = candidate_features(env)
        return decode(env, int(np.argmax(feats @ self.weights)))


def decode(env: CrossDockStream, index: int):
    candidates = env.candidates()
    return None if index == len(candidates) else candidates[index]


# --------------------------------------------------------------------- training
@dataclass
class Step:
    feats: np.ndarray
    glob: np.ndarray
    action: int
    logp: float
    value: float
    reward: float = 0.0
    gamma: float = 1.0


@dataclass
class TrainConfig:
    sizes: tuple[str, ...] = ("S", "M")
    loads: tuple[float, ...] = (0.5, 0.6, 0.7)
    demands: tuple[str, ...] = ("uniform", "skewed")
    seed_base: int = 100_000  # train pool
    measure_from: int = 30
    measure_to: int = 230
    episodes_per_iter: int = 12
    iterations: int = 120
    bc_episodes: int = 16
    bc_epochs: int = 40
    bc_lr: float = 1e-3
    ppo_epochs: int = 4
    minibatch: int = 256
    lr: float = 1e-4
    clip: float = 0.1
    entropy: float = 0.0
    critic_warmup: int = 10
    value_coef: float = 0.5
    gae_lambda: float = 0.95
    tau_sla: float = 1.0
    reward_scale: float = 1.0
    seed: int = 0
    log: list[dict] = field(default_factory=list)


def _episode_config(cfg: TrainConfig, rng: random.Random) -> StreamConfig:
    from crossdock_solver.stream.config import stream_config

    return stream_config(rng.choice(cfg.sizes), load=rng.choice(cfg.loads), demand=rng.choice(cfg.demands))


def _make_env(cfg: TrainConfig, rng: random.Random, episode: int) -> CrossDockStream:
    return CrossDockStream(
        _episode_config(cfg, rng),
        seed=cfg.seed_base + episode,
        measure_from=cfg.measure_from,
        measure_to=cfg.measure_to,
    )


def _batch(steps: list[Step]):
    n = max(len(s.feats) for s in steps)
    B = len(steps)
    feats = np.zeros((B, n, NUM_FEATURES), dtype=np.float32)
    mask = np.zeros((B, n), dtype=bool)
    for i, s in enumerate(steps):
        k = len(s.feats)
        # keep HOLD as the last real entry so `values` can find it
        feats[i, :k] = s.feats
        mask[i, :k] = True
    glob = np.stack([s.glob for s in steps])
    return torch.from_numpy(feats), torch.from_numpy(mask), torch.from_numpy(glob)


def _rollout(net: DispatchNet, env: CrossDockStream, gen: torch.Generator, scale: float, tau: float):
    steps: list[Step] = []
    times: list[float] = []
    costs: list[float] = []
    while not env.done:
        feats, glob = candidate_features(env)
        with torch.no_grad():
            x = torch.from_numpy(feats).unsqueeze(0)
            mask = torch.ones(1, len(feats), dtype=torch.bool)
            logits = net.logits(x, mask)[0]
            value = float(net.values(x, mask, torch.from_numpy(glob).unsqueeze(0))[0])
            probs = torch.softmax(logits, 0)
            index = int(torch.multinomial(probs, 1, generator=gen))
            logp = float(torch.log(probs[index] + 1e-12))
        steps.append(Step(feats, glob, index, logp, value))
        times.append(env.now)
        costs.append(env.cost_snapshot())
        action = decode(env, index)
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)
    times.append(env.now)
    costs.append(env.cost_snapshot())
    for i, step in enumerate(steps):
        step.reward = -(costs[i + 1] - costs[i]) / scale
        step.gamma = math.exp(-(times[i + 1] - times[i]) / tau)
    return steps, env.metrics()


def _advantages(steps: list[Step], lam: float) -> tuple[np.ndarray, np.ndarray]:
    adv = np.zeros(len(steps))
    running = 0.0
    for i in reversed(range(len(steps))):
        next_value = steps[i + 1].value if i + 1 < len(steps) else 0.0
        g = steps[i].gamma if i + 1 < len(steps) else 0.0
        delta = steps[i].reward + g * next_value - steps[i].value
        running = delta + g * lam * running
        adv[i] = running
    returns = adv + np.array([s.value for s in steps])
    return adv, returns


def behaviour_clone(net: DispatchNet, cfg: TrainConfig) -> float:
    opt = torch.optim.Adam(net.parameters(), lr=cfg.bc_lr)
    rng = random.Random(cfg.seed + 17)
    data: list[tuple[np.ndarray, int]] = []
    for episode in range(cfg.bc_episodes):
        env = _make_env(cfg, rng, 50_000 + episode)
        while not env.done:
            feats, _ = candidate_features(env)
            index = rule_index(env)
            data.append((feats, index))
            env.dispatch(*decode(env, index))
    loss_value = 0.0
    shuffle = random.Random(cfg.seed)
    for _ in range(cfg.bc_epochs):
        shuffle.shuffle(data)
        for start in range(0, len(data), cfg.minibatch):
            chunk = data[start : start + cfg.minibatch]
            steps = [Step(f, np.zeros(GLOBAL_FEATURES, np.float32), a, 0.0, 0.0) for f, a in chunk]
            feats, mask, _ = _batch(steps)
            actions = torch.tensor([a for _, a in chunk])
            logits = net.logits(feats, mask)
            loss = nn.functional.cross_entropy(logits, actions)
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_value = float(loss)
    return loss_value


def train(cfg: TrainConfig, *, progress=print, callback=None) -> DispatchNet:
    """BC warm start (if `bc_episodes`), then PPO. `callback(iteration, net)` runs after every update."""

    torch.manual_seed(cfg.seed)
    net = DispatchNet()
    bc_loss = behaviour_clone(net, cfg) if cfg.bc_episodes else float("nan")
    opt = torch.optim.Adam(net.parameters(), lr=cfg.lr)
    progress(f"bc done, loss={bc_loss:.4f}")
    gen = torch.Generator().manual_seed(cfg.seed)
    rng = random.Random(cfg.seed)
    episode = 0
    for iteration in range(cfg.iterations):
        start = time.perf_counter()
        batch: list[Step] = []
        adv_all: list[np.ndarray] = []
        ret_all: list[np.ndarray] = []
        objectives = []
        for _ in range(cfg.episodes_per_iter):
            env = _make_env(cfg, rng, episode)
            episode += 1
            scale = env.facility.mean_work * cfg.reward_scale
            tau = cfg.tau_sla * env.facility.sla
            steps, metrics = _rollout(net, env, gen, scale, tau)
            adv, ret = _advantages(steps, cfg.gae_lambda)
            batch.extend(steps)
            adv_all.append(adv)
            ret_all.append(ret)
            objectives.append(metrics.objective / env.facility.mean_work)
        adv = np.concatenate(adv_all)
        ret = np.concatenate(ret_all)
        adv_t = torch.tensor((adv - adv.mean()) / (adv.std() + 1e-8), dtype=torch.float32)
        ret_t = torch.tensor(ret, dtype=torch.float32)
        old_logp = torch.tensor([s.logp for s in batch], dtype=torch.float32)
        actions = torch.tensor([s.action for s in batch])
        order = np.arange(len(batch))
        perm_rng = np.random.default_rng(cfg.seed + iteration)
        for _ in range(cfg.ppo_epochs):
            perm_rng.shuffle(order)
            for begin in range(0, len(order), cfg.minibatch):
                idx = order[begin : begin + cfg.minibatch]
                feats, mask, glob = _batch([batch[i] for i in idx])
                logits = net.logits(feats, mask)
                logp_all = torch.log_softmax(logits, -1)
                logp = logp_all.gather(1, actions[idx].unsqueeze(1)).squeeze(1)
                ratio = torch.exp(logp - old_logp[idx])
                a = adv_t[idx]
                policy_loss = -torch.min(ratio * a, ratio.clamp(1 - cfg.clip, 1 + cfg.clip) * a).mean()
                probs = logp_all.exp()
                entropy = -(probs * logp_all.masked_fill(~mask, 0.0)).sum(-1).mean()
                value = net.values(feats, mask, glob)
                value_loss = ((value - ret_t[idx]) ** 2).mean()
                if iteration < cfg.critic_warmup:
                    loss = cfg.value_coef * value_loss  # critic warm-up: policy frozen
                else:
                    loss = policy_loss + cfg.value_coef * value_loss - cfg.entropy * entropy
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 1.0)
                opt.step()
        record = {
            "iteration": iteration,
            "steps": len(batch),
            "objective_norm": float(np.mean(objectives)),
            "entropy": float(entropy),
            "sec": time.perf_counter() - start,
        }
        cfg.log.append(record)
        progress(
            f"it {iteration:3d} steps={record['steps']:5d} J/work={record['objective_norm']:.3f} "
            f"entropy={record['entropy']:.3f} {record['sec']:.1f}s"
        )
        if callback is not None:
            callback(iteration, net)
    return net


# ------------------------------------------------------- policy distillation
def candidate_index(env: CrossDockStream, action) -> int:
    """Index of `action` (None = HOLD) in the candidate list of `env`."""

    candidates = env.candidates()
    if action is None:
        return len(candidates)
    truck, door, destination = action
    trucks = env.yard[: env.max_candidates]
    doors = env.free_doors()
    D = env.config.num_destinations
    return (trucks.index(truck) * len(doors) + doors.index(door)) * D + destination


def collect_labels(
    net: DispatchNet | None,
    teacher,
    env: CrossDockStream,
    *,
    beta: float,
    rng: random.Random,
) -> list[tuple[np.ndarray, int]]:
    """DAgger: the teacher labels every visited state; the executed action is the
    teacher's with probability `beta`, otherwise the current network's."""

    data: list[tuple[np.ndarray, int]] = []
    learner = RLPolicy(net) if net is not None else None
    if hasattr(teacher, "reset"):
        teacher.reset(env)
    while not env.done:
        feats, _ = candidate_features(env)
        target = teacher.act(env)
        data.append((feats, candidate_index(env, target)))
        action = target if learner is None or rng.random() < beta else learner.act(env)
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)
    return data


def fit_classifier(net: DispatchNet, data: list[tuple[np.ndarray, int]], *, epochs: int, lr: float, seed: int) -> float:
    opt = torch.optim.Adam(net.score.parameters(), lr=lr)
    order = list(range(len(data)))
    shuffle = random.Random(seed)
    loss_value = float("nan")
    for _ in range(epochs):
        shuffle.shuffle(order)
        for start in range(0, len(order), 256):
            chunk = [data[i] for i in order[start : start + 256]]
            steps = [Step(f, np.zeros(GLOBAL_FEATURES, np.float32), a, 0.0, 0.0) for f, a in chunk]
            feats, mask, _ = _batch(steps)
            actions = torch.tensor([a for _, a in chunk])
            loss = nn.functional.cross_entropy(net.logits(feats, mask), actions)
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_value = float(loss)
    return loss_value


def collect_soft_labels(
    net: DispatchNet | None,
    teacher,
    env: CrossDockStream,
    *,
    beta: float,
    rng: random.Random,
    temperature: float,
) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """DAgger with cost-sensitive targets: the rollout teacher scores its whole
    shortlist and the target is softmax(-(cost - min) / (temperature * spread))
    over those candidates (spread = std of the shortlist costs), so actions the
    teacher finds nearly as good keep probability mass. With an oracle teacher
    this is hindsight learning with hindsight action costs (Sinclair et al. 2022)
    instead of the hindsight argmax."""

    from crossdock_solver.stream.rollout import shortlist

    data: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    learner = RLPolicy(net) if net is not None else None
    if hasattr(teacher, "reset"):
        teacher.reset(env)
    while not env.done:
        feats, _ = candidate_features(env)
        actions = shortlist(env, teacher.extra_trucks)
        costs = teacher.scores(env, actions)
        teacher._step += 1
        index = np.array([candidate_index(env, a) for a in actions])
        spread = max(float(np.std(costs)), 1e-9)
        logits = -(costs - costs.min()) / (temperature * spread)
        target = np.exp(logits - logits.max())
        target /= target.sum()
        data.append((feats, index, target.astype(np.float32)))
        best = actions[int(np.argmin(costs))]
        action = best if learner is None or rng.random() < beta else learner.act(env)
        if action is None:
            env.hold()
        else:
            env.dispatch(*action)
    return data


def fit_soft(net: DispatchNet, data: list[tuple[np.ndarray, np.ndarray, np.ndarray]], *, epochs: int, lr: float,
             seed: int) -> float:
    """Cross-entropy against the soft targets (candidates outside the teacher's
    shortlist get target 0)."""

    opt = torch.optim.Adam(net.score.parameters(), lr=lr)
    order = list(range(len(data)))
    shuffle = random.Random(seed)
    loss_value = float("nan")
    for _ in range(epochs):
        shuffle.shuffle(order)
        for start in range(0, len(order), 256):
            chunk = [data[i] for i in order[start : start + 256]]
            steps = [Step(f, np.zeros(GLOBAL_FEATURES, np.float32), 0, 0.0, 0.0) for f, _, _ in chunk]
            feats, mask, _ = _batch(steps)
            target = torch.zeros(mask.shape)
            for row, (_, index, probs) in enumerate(chunk):
                target[row, torch.from_numpy(index)] = torch.from_numpy(probs)
            logp = torch.log_softmax(net.logits(feats, mask), dim=1)
            loss = -(target * logp.masked_fill(~mask, 0.0)).sum(1).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
            loss_value = float(loss)
    return loss_value

