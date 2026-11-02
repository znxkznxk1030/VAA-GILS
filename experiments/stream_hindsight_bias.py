"""C2: direct measurement of hindsight bias in the teacher labels.

Why hindsight learning failed here (stream_rl_research.md 5.7): a label taken
from ONE future (the real one, or one sample) is the best action for that
future, not for the state. This script measures how far apart the two are.

At states visited by the Rollout teacher (12 tuning streams, after an FCFS-VAA
warm-up) every shortlisted action (rollout.shortlist: head truck x every
destination, the next two trucks' rule actions, HOLD) is simulated for one SLA
under K = 40 futures with common random numbers (the same future for every
action), base policy FCFS-VAA, exactly as in the Rollout teacher. A future
drawn by fork(seed) has the distribution of the real future given the state,
so a one-future label is distributed as the real-future (hindsight) label of
5.7.

  C[k, a]  cost accrued over the horizon under future k after action a
  a*       argmin_a mean_k C[k, a] over the HELD-OUT futures 16..39
  label_m  argmin_a mean over a group of m futures from the label pool 0..15
           (m = 1 is the hindsight label, m = 8 the Rollout teacher's label)

Reported per m: agreement P(label_m = a*), regret E[Cbar(label_m) - Cbar(a*)]
(Cbar on held-out futures), and normalized regret = regret / (mean_a Cbar(a) -
Cbar(a*)), i.e. 0 = the expected-cost-best action, 1 = a uniformly random
shortlist action. Also the hindsight bias of the value
(E_k min_a C - min_a E_k C), and how the hindsight label depends on the
realized time to the next arrival. Confidence intervals: bootstrap over
streams (clusters).

Usage:
    python experiments/stream_hindsight_bias.py --workers 4
    python experiments/stream_hindsight_bias.py --summary
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from crossdock_solver.stream.config import stream_config
from crossdock_solver.stream.policies import FCFSRulePolicy
from crossdock_solver.stream.rollout import RolloutPolicy, shortlist
from crossdock_solver.stream.sim import ARRIVE, CrossDockStream, step

OUTPUT = ROOT / "outputs" / "stream_hindsight_bias.jsonl"
SUMMARY = ROOT / "outputs" / "stream_hindsight_bias.txt"
TUNING_BASE = 200_000  # same 12 tuning streams as every other selection (stream_rl_train.TUNING_SET)
TUNING_SET = [(size, load, demand) for size in ("S", "M") for load in (0.5, 0.6, 0.7)
              for demand in ("uniform", "skewed")]
WARMUP = 150  # FCFS-VAA decisions before the teacher takes over
DECISIONS = 240  # teacher decisions per stream
EVERY = 2  # measure every 2nd teacher decision -> 120 states per stream
FUTURES = 40
LABEL_POOL = 16  # futures 0..15 make labels, 16..39 judge them
GROUPS = (1, 2, 4, 8, 16)
BOOT = 5_000


def action_kind(env: CrossDockStream, action) -> str:
    if action is None:
        return "hold"
    return "head" if action[0] is env.yard[0] else "later"


def cost_matrix(env: CrossDockStream, actions: list, seeds: list[int]) -> tuple[np.ndarray, list[float]]:
    base = FCFSRulePolicy()
    until = env.now + env.facility.sla
    costs = np.zeros((len(seeds), len(actions)))
    next_arrival = []
    for i, seed in enumerate(seeds):
        for j, action in enumerate(actions):
            sim = env.fork(seed, until)
            if j == 0:
                arrivals = [e[0] for e in sim._events if e[2] == ARRIVE]
                next_arrival.append((min(arrivals) - env.now) * env.facility.arrival_rate if arrivals else float("inf"))
            start = sim.cost_snapshot()
            if action is None:
                sim.hold()
            else:
                truck, door, destination = action
                sim.dispatch(sim.truck_by_uid(truck.uid), door, destination)
            while not sim.done:
                step(sim, base)
            costs[i, j] = sim.cost_snapshot() - start
    return costs, next_arrival


def _job(k: int) -> list[dict]:
    size, load, demand = TUNING_SET[k]
    env = CrossDockStream(stream_config(size, load=load, demand=demand), seed=TUNING_BASE + k,
                          measure_from=100, measure_to=500)
    rule = FCFSRulePolicy()
    for _ in range(WARMUP):
        step(env, rule)
    teacher = RolloutPolicy(seed=k)
    teacher.reset(env)
    rows = []
    for d in range(DECISIONS):
        if env.done:
            break
        if d % EVERY == 0:
            actions = shortlist(env)
            seeds = [(k * 1_000_003 + d * 97 + i * 7_919 + 12_345) & 0x7FFFFFFF for i in range(FUTURES)]
            start = time.perf_counter()
            costs, next_arrival = cost_matrix(env, actions, seeds)
            open_units = float(sum(lot.units for lots in env.open_lots for lot in lots))
            rows.append({
                "cell": k, "size": size, "load": load, "demand": demand, "decision": d,
                "kinds": [action_kind(env, a) for a in actions],
                "yard": len(env.yard), "free_doors": len(env.free_doors()),
                "open_units": open_units / env.facility.mean_units,
                "next_arrival": next_arrival,  # realized time to the next arrival, in mean interarrival times
                "costs": np.round(costs / env.facility.mean_work, 5).tolist(),  # in truck-work x trucks units
                "seconds": time.perf_counter() - start,
            })
        step(env, teacher)
    return rows


def run(workers: int) -> None:
    done = set()
    if OUTPUT.exists():
        done = {json.loads(line)["cell"] for line in OUTPUT.read_text().splitlines() if line}
    jobs = [k for k in range(len(TUNING_SET)) if k not in done]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with multiprocessing.Pool(workers) as pool, OUTPUT.open("a") as sink:
        for rows in pool.imap_unordered(_job, jobs):
            for row in rows:
                sink.write(json.dumps(row) + "\n")
            sink.flush()
            print(f"cell {rows[0]['cell']:2} {rows[0]['size']} {rows[0]['load']} {rows[0]['demand']:8} "
                  f"{len(rows)} states, {np.mean([r['seconds'] for r in rows]):.2f}s per state", flush=True)


# ------------------------------------------------------------------ analysis
def per_state(row: dict) -> dict:
    C = np.array(row["costs"])
    pool, held = C[:LABEL_POOL], C[LABEL_POOL:]
    mean_held = held.mean(axis=0)
    best = int(np.argmin(mean_held))
    spread = float(mean_held.mean() - mean_held[best])
    out = {"best": best, "best_kind": row["kinds"][best], "spread": spread}
    for m in GROUPS:
        labels = [int(np.argmin(pool[g * m:(g + 1) * m].mean(axis=0))) for g in range(LABEL_POOL // m)]
        regret = np.array([mean_held[a] - mean_held[best] for a in labels])
        out[f"agree{m}"] = float(np.mean([a == best for a in labels]))
        out[f"regret{m}"] = float(regret.mean())
        out[f"nregret{m}"] = float(regret.mean() / spread) if spread > 1e-9 else np.nan
        if m == 1:
            out["labels1"] = labels
    # hindsight bias of the value, all futures
    out["hb"] = float(C.min(axis=1).mean() - C.mean(axis=0).min())
    out["hb_rel"] = float(out["hb"] / spread) if spread > 1e-9 else np.nan
    # how often the hindsight-best action differs between futures: distinct labels among 16
    out["distinct1"] = len(set(out["labels1"]))
    return out


def cluster_ci(values: np.ndarray, clusters: np.ndarray, rng) -> tuple[float, float]:
    ids = np.unique(clusters)
    groups = [values[clusters == c] for c in ids]
    means = []
    for _ in range(BOOT):
        pick = rng.integers(0, len(ids), size=len(ids))
        sample = np.concatenate([groups[i] for i in pick])
        sample = sample[~np.isnan(sample)]
        means.append(sample.mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize() -> str:
    rng = np.random.default_rng(0)
    rows = [json.loads(line) for line in OUTPUT.read_text().splitlines() if line]
    stats = [per_state(r) for r in rows]
    cells = np.array([r["cell"] for r in rows])
    ties = np.array([s["spread"] <= 1e-9 for s in stats])
    out = [f"Hindsight bias of teacher labels: {len(rows)} teacher states from {len(set(cells))} tuning streams, "
           f"{FUTURES} common futures per state ({LABEL_POOL} make labels, {FUTURES - LABEL_POOL} judge them)",
           f"states where every shortlisted action has the same cost: {ties.sum()} (left out of normalized regret)", ""]

    curve: dict[str, list] = {}

    def line(name: str, key: str, fmt: str) -> None:
        vals = np.array([s[key] for s in stats], dtype=float)
        lo, hi = cluster_ci(vals, cells, rng)
        mean = np.nanmean(vals)
        curve.setdefault(key.rstrip("0123456789"), []).append((mean, lo, hi))
        out.append(f"  {name:34} {format(mean, fmt):>8}  [95% CI {format(lo, fmt)}, {format(hi, fmt)}]")

    out.append("Label quality vs futures per label (m = 1: hindsight label, m = 8: Rollout teacher label)")
    for m in GROUPS:
        out.append(f" m = {m}")
        line("agreement with a*", f"agree{m}", ".1%")
        line("normalized regret (0 best, 1 random)", f"nregret{m}", ".3f")
    out.append("")
    out.append("Value hindsight bias  E_k min_a C - min_a E_k C  (relative to the random-action regret)")
    line("hindsight bias / spread", "hb_rel", ".2f")
    line("distinct hindsight labels among 16 futures", "distinct1", ".2f")
    out.append(f"  shortlist size: mean {np.mean([len(r['kinds']) for r in rows]):.1f}")
    out.append("")

    out.append("By the expected-cost-best action a* (share of states, m = 1 / m = 8 agreement)")
    for kind in ("head", "later", "hold"):
        idx = [i for i, s in enumerate(stats) if s["best_kind"] == kind]
        if not idx:
            continue
        out.append(f"  a* = {kind:6} {len(idx) / len(stats):6.1%}   agree m=1 {np.mean([stats[i]['agree1'] for i in idx]):6.1%}"
                   f"   m=8 {np.mean([stats[i]['agree8'] for i in idx]):6.1%}"
                   f"   norm. regret m=1 {np.nanmean([stats[i]['nregret1'] for i in idx]):.3f}"
                   f" m=8 {np.nanmean([stats[i]['nregret8'] for i in idx]):.3f}")
    pending = np.array([r["open_units"] > 0 for r in rows])
    for flag, name in ((True, "freight waiting for a carrier"), (False, "no freight waiting")):
        idx = np.where(pending == flag)[0]
        out.append(f"  {name:30} {len(idx) / len(rows):6.1%}   agree m=1 {np.mean([stats[i]['agree1'] for i in idx]):6.1%}"
                   f"   m=8 {np.mean([stats[i]['agree8'] for i in idx]):6.1%}")
    out.append("")

    out.append("Hindsight label vs the realized time to the next arrival (m = 1 labels; terciles of that time)")
    gaps, holds, agrees, heads = [], [], [], []
    for r, s in zip(rows, stats):
        for i, a in enumerate(s["labels1"]):
            gaps.append(r["next_arrival"][i])
            holds.append(r["kinds"][a] == "hold")
            heads.append(r["kinds"][a] == "head")
            agrees.append(a == s["best"])
    gaps, holds, agrees, heads = map(np.array, (gaps, holds, agrees, heads))
    cuts = np.quantile(gaps, [1 / 3, 2 / 3])
    bins = np.digitize(gaps, cuts)
    for b, name in enumerate(("next truck soon", "middle", "next truck late")):
        sel = bins == b
        out.append(f"  {name:16} (gap {np.median(gaps[sel]):.2f})  label HOLD {holds[sel].mean():6.1%}"
                   f"   label head truck {heads[sel].mean():6.1%}   agree with a* {agrees[sel].mean():6.1%}")
    from scipy.stats import chi2_contingency

    table = np.array([[np.sum((bins == b) & holds), np.sum((bins == b) & ~holds)] for b in range(3)])
    out.append(f"  HOLD label depends on the realized next arrival: chi2 p = {chi2_contingency(table).pvalue:.2g}")
    held = np.array([s["best_kind"] == "hold" for s in stats])
    out.append(f"  for comparison, a* is HOLD in {held.mean():.1%} of states")
    out.append("  (labels of one state are counted 16 times, so this p overstates the evidence)")
    text = "\n".join(out)
    SUMMARY.write_text(text + "\n")
    plot(curve)
    return text


def plot(curve: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, blue = "#1a1a1a", "#6b6b6b", "#d9d9d9", "#2b6cb0"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": muted,
                         "xtick.color": muted, "ytick.color": muted, "axes.labelcolor": ink})
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.4))
    for ax, key, ylabel, scale in ((axes[0], "agree", "agreement with a* (%)", 100),
                                   (axes[1], "nregret", "normalized regret", 1)):
        vals = np.array(curve[key]) * scale
        ax.plot(GROUPS, vals[:, 0], color=blue, lw=2, marker="o", ms=5, zorder=3)
        ax.fill_between(GROUPS, vals[:, 1], vals[:, 2], color=blue, alpha=0.15, lw=0, zorder=2)
        ax.set_xscale("log", base=2)
        ax.set_xticks(GROUPS, [str(m) for m in GROUPS])
        ax.set_xlabel("futures per label m")
        ax.set_ylabel(ylabel)
        ax.yaxis.grid(True, color=grid, lw=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for m, v in zip(GROUPS, vals[:, 0]):
            if m in (1, 8):
                tag = "hindsight" if m == 1 else "Rollout"
                ax.annotate(f"{tag}\n{v:.1f}" if scale == 100 else f"{tag}\n{v:.2f}", (m, v),
                            textcoords="offset points", xytext=(6, -20 if key == "agree" else 4), fontsize=7, color=ink)
    axes[0].set_ylim(44, 86)
    axes[0].set_title("(a) label agrees with the expected-cost best", fontsize=8.5, loc="left", color=ink)
    axes[1].set_title("(b) regret (0 best, 1 random action)", fontsize=8.5, loc="left", color=ink)
    fig.tight_layout(w_pad=1.5)
    figure = ROOT / "paper" / "figures" / "stream_hindsight_bias"
    figure.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(figure.with_suffix(".pdf"))
    fig.savefig(figure.with_suffix(".png"), dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    if not args.summary:
        run(args.workers)
    print(summarize())


if __name__ == "__main__":
    main()
