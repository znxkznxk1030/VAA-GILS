#!/usr/bin/env python3
"""Black-background charts and diagrams for the October 2026 progress talk.

Writes SVG (and PNG via headless Chrome at 2x) to outputs/slides/:

  prev_gap.svg        previous study: mean gap to best observed solution (JKIIE Table 4)
  stream_relative.svg stream study: J relative to the FCFS rule per size (outputs/stream_eval.jsonl)
  compound_flow.svg   compound-truck process diagram
  static_vs_stream.svg |I|+|F| = |D| (one closed batch) vs |I|+|F| >> |D| (endless stream)

matplotlib is unusable in this environment (NumPy ABI), so SVG is written directly.
Palette: dark categorical slots validated on #000000 (dataviz validate_palette.js).

Usage:
    python experiments/make_slide_charts.py
"""

from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import shutil
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "slides"

BG = "#000000"
INK = "#ffffff"
INK2 = "#c3c2b7"
MUTED = "#898781"
GRID = "#2c2c2a"
AXIS = "#c3c2b7"
BLUE, ORANGE, AQUA = "#3987e5", "#d95926", "#199e70"
GRAY_BAR = "#5c5b57"
FONT = "'Helvetica Neue', 'Apple SD Gothic Neo', sans-serif"

# JKIIE Table 4: mean gap to the best observed solution (%) over the 9 conditions,
# 20 test instances x 5 replications each. SA-RL5 = Paper-SA-RL5 (none) or
# Extended SA-RL5 (medium/tight).
PREV_TABLE4 = {
    "VAA": [6.61, 3.90, 2.91, 3.72, 2.58, 1.26, 2.17, 1.57, 0.78],
    "SA-RL5": [1.07, 0.97, 0.61, 1.98, 1.65, 0.99, 1.94, 1.46, 0.74],
    "VAA-GILS": [0.23, 0.17, 0.11, 0.28, 0.25, 0.13, 0.15, 0.11, 0.06],
}


def svg(width: int, height: int, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">'
        f'<rect width="{width}" height="{height}" fill="{BG}"/>{body}</svg>'
    )


def text(x, y, s, size=28, fill=INK, anchor="start", weight=700) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>'
    )


def est_width(s: str, size: float) -> float:
    """Rough rendered width: Hangul ~0.95em, other glyphs ~0.58em."""

    return sum(size * (0.95 if "\uac00" <= ch <= "\ud7a3" else 0.58) for ch in s)


def hbar(x0, y, length, h, fill) -> str:
    """Horizontal bar anchored at x0, square at the baseline, 4px round at the data end."""

    r = min(4, length / 2, h / 2)
    x1 = x0 + length
    return (
        f'<path d="M{x0},{y} H{x1 - r} Q{x1},{y} {x1},{y + r} V{y + h - r} '
        f'Q{x1},{y + h} {x1 - r},{y + h} H{x0} Z" fill="{fill}"/>'
    )


def vbar(x, zero_y, value_y, w, fill) -> str:
    """Vertical bar from the zero line to value_y; rounded at the data end."""

    r = min(4, abs(value_y - zero_y) / 2, w / 2)
    if value_y < zero_y:  # upward
        return (
            f'<path d="M{x},{zero_y} V{value_y + r} Q{x},{value_y} {x + r},{value_y} '
            f'H{x + w - r} Q{x + w},{value_y} {x + w},{value_y + r} V{zero_y} Z" fill="{fill}"/>'
        )
    return (
        f'<path d="M{x},{zero_y} V{value_y - r} Q{x},{value_y} {x + r},{value_y} '
        f'H{x + w - r} Q{x + w},{value_y} {x + w},{value_y - r} V{zero_y} Z" fill="{fill}"/>'
    )


def prev_gap_chart() -> str:
    width, height = 1100, 430
    rows = [(name, statistics.mean(vals)) for name, vals in PREV_TABLE4.items()]
    left, right, top = 260, 980, 40
    bar_h, gap = 72, 34
    scale = (right - left) / 3.0
    parts = []
    for tick in (0, 1, 2, 3):
        x = left + tick * scale
        parts.append(f'<line x1="{x}" y1="{top - 10}" x2="{x}" y2="{top + 3 * (bar_h + gap) - gap + 10}" stroke="{GRID}" stroke-width="1.5"/>')
        parts.append(text(x, top + 3 * (bar_h + gap) + 30, f"{tick}%", 24, MUTED, "middle", 500))
    for i, (name, value) in enumerate(rows):
        y = top + i * (bar_h + gap)
        fill = BLUE if name == "VAA-GILS" else GRAY_BAR
        label = "VAA-GILS (제안)" if name == "VAA-GILS" else ("SA-RL5 (원 모델)" if name == "SA-RL5" else "VAA (초기해)")
        parts.append(text(left - 24, y + bar_h / 2 + 10, label, 30, INK, "end"))
        parts.append(hbar(left, y, max(value * scale, 6), bar_h, fill))
        parts.append(text(left + value * scale + 16, y + bar_h / 2 + 11, f"{value:.2f}%", 32, INK, "start"))
    parts.append(f'<line x1="{left}" y1="{top - 10}" x2="{left}" y2="{top + 3 * (bar_h + gap) - gap + 10}" stroke="{AXIS}" stroke-width="2"/>')
    parts.append(text(left, height - 12, "관측 최선해 대비 평균 격차 · 9개 조건 × 20개 인스턴스 · 낮을수록 좋음", 22, MUTED, "start", 500))
    return svg(width, height, "".join(parts))


def stream_values() -> dict[str, dict[str, float]]:
    records = [json.loads(line) for line in (ROOT / "outputs" / "stream_eval.jsonl").read_text().splitlines() if line]
    by = {(r["method"], r["size"], r["load"], r["demand"], r["rep"]): r for r in records}
    ratios: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (method, size, load, demand, rep), r in by.items():
        base = by.get(("FCFS-VAA", size, load, demand, rep))
        if base is None:
            continue
        ratios[(method, size)].append(100 * (r["objective"] / base["objective"] - 1))
    return {
        method: {size: statistics.mean(ratios[(method, size)]) for size in ("S", "M", "L")}
        for method in ("Cyclic-GILS", "RL-API", "Rollout")
    }


def stream_chart() -> str:
    values = stream_values()
    width, height = 1240, 660
    left, right, top, bottom = 120, 1210, 110, 560
    lo, hi = -30.0, 40.0
    y_of = lambda v: top + (hi - v) / (hi - lo) * (bottom - top)  # noqa: E731
    series = [
        ("Cyclic-GILS", "Cyclic VAA-GILS (기존 해법)", ORANGE),
        ("RL-API", "강화학습 증류 정책", BLUE),
        ("Rollout", "강화학습 Rollout", AQUA),
    ]
    parts = []
    # legend (one row above the plot)
    lx = left
    for _, label, color in series:
        parts.append(f'<rect x="{lx}" y="28" width="26" height="26" rx="4" fill="{color}"/>')
        parts.append(text(lx + 38, 51, label, 26, INK, "start", 600))
        lx += 38 + est_width(label, 26) + 48
    for tick in range(-30, 41, 10):
        y = y_of(tick)
        stroke = AXIS if tick == 0 else GRID
        sw = 2.5 if tick == 0 else 1.5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="{stroke}" stroke-width="{sw}"/>')
        parts.append(text(left - 16, y + 8, f"{tick:+d}%" if tick else "0", 22, MUTED, "end", 500))
    parts.append(text(right, y_of(0) - 12, "FCFS 규칙 = 0", 22, INK2, "end", 600))
    groups = [("S", "S"), ("M", "M"), ("L", "L (학습 미사용)")]
    group_w = (right - left) / 3
    bar_w = 92
    for gi, (size, label) in enumerate(groups):
        cx = left + group_w * (gi + 0.5)
        x0 = cx - (3 * bar_w + 2 * 4) / 2
        for si, (key, _, color) in enumerate(series):
            v = values[key][size]
            x = x0 + si * (bar_w + 4)
            vy = y_of(v)
            parts.append(vbar(x, y_of(0), vy, bar_w, color))
            ty = vy - 12 if v > 0 else vy + 32
            parts.append(text(x + bar_w / 2, ty, f"{v:+.1f}%", 24, INK, "middle", 700))
        parts.append(text(cx, bottom + 52, label, 28, INK, "middle", 700))
    parts.append(text(left, height - 8, "FCFS 규칙 대비 목적값 J 변화 · 시험 스트림 90개 · 낮을수록 좋음", 22, MUTED, "start", 500))
    return svg(width, height, "".join(parts))


def compound_flow() -> str:
    width, height = 1720, 330
    steps = [
        ("① 도착", "여러 목적지 화물 적재"),
        ("② 부분 하역", "유지 목적지 d 외 화물만"),
        ("③ 이송 화물 대기", "다른 트럭이 내린 d행 화물"),
        ("④ 출고 전환", "d의 운송 트럭으로 출발"),
    ]
    box_w, box_h, gap = 360, 170, 76
    y = 60
    parts = []
    for i, (title, sub) in enumerate(steps):
        x = 20 + i * (box_w + gap)
        stroke = BLUE if i == 3 else INK
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="18" fill="none" stroke="{stroke}" stroke-width="4"/>')
        parts.append(text(x + box_w / 2, y + 74, title, 36, INK, "middle", 800))
        parts.append(text(x + box_w / 2, y + 124, sub, 26, INK2, "middle", 500))
        if i < 3:
            ax = x + box_w + 12
            parts.append(f'<line x1="{ax}" y1="{y + box_h / 2}" x2="{ax + gap - 30}" y2="{y + box_h / 2}" stroke="{INK}" stroke-width="4"/>')
            parts.append(f'<path d="M{ax + gap - 24},{y + box_h / 2} l-18,-12 v24 z" fill="{INK}"/>')
    parts.append(text(width / 2, y + box_h + 72, "같은 목적지를 공유하는 트럭끼리 지연이 전파된다", 30, INK2, "middle", 600))
    return svg(width, height, "".join(parts))


def static_vs_stream() -> str:
    width, height = 1720, 560
    parts = []

    def truck(x, y, color=INK, w=56, h=36):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" stroke="{color}" stroke-width="3"/>'

    def dest(x, y, label):
        return (
            f'<circle cx="{x}" cy="{y}" r="30" fill="none" stroke="{BLUE}" stroke-width="4"/>'
            + text(x, y + 9, label, 24, INK, "middle", 700)
        )

    def arrow(x1, y1, x2, y2, color=MUTED):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.5"/>'

    # left: one closed batch, one carrier per destination
    parts.append(text(40, 50, "기존 모형 (산업공학회 투고)", 34, INK, "start", 800))
    parts.append(text(40, 92, "I + F = D · 한 번의 닫힌 배치", 28, INK2, "start", 600))
    for i in range(4):
        ty = 150 + i * 90
        parts.append(truck(80, ty))
        parts.append(arrow(140, ty + 18, 380, ty + 18))
        parts.append(dest(420, ty + 18, f"D{i + 1}"))
    parts.append(text(40, 530, "목적지마다 운송 트럭 정확히 1대", 26, MUTED, "start", 500))

    # divider
    parts.append(f'<line x1="640" y1="40" x2="640" y2="520" stroke="{GRID}" stroke-width="2"/>')

    # right: endless stream, many carriers per destination
    parts.append(text(700, 50, "새 환경 (연구 중)", 34, INK, "start", 800))
    parts.append(text(700, 92, "I + F ≫ D · 트럭이 끝없이 도착", 28, INK2, "start", 600))
    dest_y = [168, 258, 348, 438]
    for i, dy in enumerate(dest_y):
        parts.append(dest(1620, dy, f"D{i + 1}"))
    pattern = [0, 2, 1, 0, 3, 0, 1, 2, 0, 3, 1, 0]
    for k, d in enumerate(pattern):
        x = 720 + (k % 6) * 120
        y = 160 + (k // 6) * 210 + (k % 2) * 40
        color = INK if k < 10 else MUTED
        parts.append(truck(x, y, color))
        parts.append(arrow(x + 56, y + 18, 1588, dest_y[d], "#4a4945"))
    parts.append(f'<line x1="720" y1="488" x2="1380" y2="488" stroke="{MUTED}" stroke-width="2.5"/>')
    parts.append(f'<path d="M1392,488 l-16,-9 v18 z" fill="{MUTED}"/>')
    parts.append(text(1404, 497, "시간", 24, MUTED, "start", 600))
    parts.append(text(1240, 540, "목적지 하나를 여러 트럭이 나눠 맡고, 화물은 도크에 쌓였다가 다음 트럭에 실린다", 26, MUTED, "middle", 500))
    return svg(width, height, "".join(parts))


def render_png(svg_path: Path, width: int, height: int) -> None:
    chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if not chrome.exists():
        return
    html = svg_path.with_suffix(".html")
    html.write_text(
        f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:{BG}}}</style>'
        + svg_path.read_text()
    )
    png = svg_path.with_suffix(".png")
    subprocess.run(
        [
            str(chrome), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=2", f"--window-size={width},{height}",
            f"--screenshot={png}", html.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    html.unlink()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    charts = {
        "prev_gap": (prev_gap_chart(), 1100, 430),
        "stream_relative": (stream_chart(), 1240, 660),
        "compound_flow": (compound_flow(), 1720, 330),
        "static_vs_stream": (static_vs_stream(), 1720, 560),
    }
    for name, (content, width, height) in charts.items():
        path = OUT / f"{name}.svg"
        path.write_text(content)
        render_png(path, width, height)
        print(f"wrote {path.relative_to(ROOT)}")
    print("stream values (% vs FCFS):", json.dumps(stream_values(), indent=1))


if __name__ == "__main__":
    main()
