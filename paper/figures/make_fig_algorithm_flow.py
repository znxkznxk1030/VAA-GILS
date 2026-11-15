"""Flowchart of VAA-GILS (Algorithm 1). Line numbers refer to
docs/revision_drafts/R1-11_R2-9_algorithm1_pseudocode.md.

    python3 make_fig_algorithm_flow.py fig_algorithm_flow.drawio
"""
import sys
from xml.sax.saxutils import escape

INK, GREY, LINE = "#1A1A1A", "#4D4D4D", "#4D4D4D"
SHADE = "#D9DEE3"          # shared palette with fig0_compound_timeline
BAND = "#F6F6F6"
FONT = "fontFamily=Helvetica;"
cells, n = [], [0]


def nid():
    n[0] += 1
    return f"c{n[0]}"


def box(x, y, w, h, style, value=""):
    cells.append(
        f'<mxCell id="{nid()}" parent="1" vertex="1" style="{style}" '
        f'value="{escape(value, {chr(34): "&quot;"})}">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    )


def text(x, y, w, h, value, size=10, align="center", color=INK, bold=False, italic=False):
    fs = (1 if bold else 0) + (2 if italic else 0)
    box(x, y, w, h,
        f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;"
        f"whiteSpace=wrap;fontSize={size};fontColor={color};fontStyle={fs};{FONT}", value)


def arrow(pts, head=True):
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
    end = "endArrow=block;endFill=1;endSize=5;" if head else "endArrow=none;"
    st = f"{end}html=1;rounded=0;strokeColor={LINE};strokeWidth=1.3;"
    cells.append(
        f'<mxCell id="{nid()}" parent="1" edge="1" style="{st}"><mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/>'
        f'<Array as="points">{mid}</Array></mxGeometry></mxCell>'
    )


def ln(s):
    return ""


def small(s):
    return f"<br><span style='font-size:8.5px;color:{GREY}'>{s}</span>"


def step(x, y, w, h, value, shaded=False, fill=None):
    box(x, y, w, h,
        f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill or (SHADE if shaded else '#FFFFFF')};"
        f"strokeColor={LINE};strokeWidth=1.3;fontSize=10.5;fontColor={'#FFFFFF' if fill == '#4E8D8C' else INK};{FONT}", value)


def decision(cx, cy, value, w=196, h=62):
    box(cx - w / 2, cy - h / 2, w, h,
        f"rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=1.3;"
        f"fontSize=10.5;fontColor={INK};{FONT}", value)


def terminal(cx, y, value):
    box(cx - 55, y, 110, 22,
        f"rounded=0;whiteSpace=wrap;html=1;fillColor=#355C7D;strokeColor=#4D4D4D;"
        f"fontSize=10.5;fontColor=#FFFFFF;fontStyle=1;{FONT}", value)


def band(y, h, label):
    box(10, y, 540, h, f"rounded=0;html=1;fillColor={BAND};strokeColor=#CCCCCC;strokeWidth=1;")
    text(16, y + 3, 130, 14, label, 9, "left", GREY, italic=True)


s, sp, sb = "<i>s</i>", "<i>s′</i>", "<i>s</i>*"
J = lambda a: f"<i>J</i>({a})"
CX, W = 200, 214          # main column
X0 = CX - W / 2
SX, SW = 346, 194         # side column (yes-branches)
SCX = SX + SW / 2
LOOPX = 44

# ---------------- bands
band(40, 112, "Initialization")
band(160, 452, "Iterated search")
band(620, 62, "Termination")

# ---------------- nodes
terminal(CX, 10, "Start")
step(X0, 58, W, 34, f"Construct initial solution {s} by VAA{ln('1')}")
step(X0, 108, W, 34, f"{s} ← Descent({s});&nbsp; {sb} ← {s}{ln('2–3')}<br><i>c</i> ← 0;&nbsp; <i>n</i> ← 1{ln('3–4')}", shaded=True)

step(X0, 182, W, 42, f"Select operator uniformly<br>Generate candidate {sp} from {s}{ln('5–6')}")
# operator set panel: where the bottleneck-guided operators enter
ACC, ACCL = "#355C7D", "#355C7D"
PY = 162
box(SX, PY, SW, 16,
    f"rounded=0;whiteSpace=wrap;html=1;fillColor=#9AA9B5;strokeColor=#4D4D4D;fontSize=9;fontColor=#FFFFFF;fontStyle=1;{FONT}",
    "Operator set Ω: 11 operators")
box(SX, PY + 16, SW, 28,
    f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=1;fontSize=9;fontColor={INK};{FONT}",
    "7 generic: k1–k4, k6–k8<br>4 guided: g1–g4; each operator: 1/11")
box(SX, PY + 44, SW, 42,
    f"rounded=0;whiteSpace=wrap;html=1;fillColor={ACCL};strokeColor={ACC};strokeWidth=2.5;fontSize=9;fontColor=#FFFFFF;{FONT}",
    "<b>4 bottleneck-guided operators (g1–g4)</b><br>"
    "Identify bottleneck → evaluate moves<br>Return the best improving move")
cells.append(f'<mxCell id="{nid()}" parent="1" edge="1" style="endArrow=none;html=1;rounded=0;'
             f'strokeColor={LINE};strokeWidth=1.3;dashed=1;dashPattern=3 3;"><mxGeometry relative="1" as="geometry">'
             f'<mxPoint x="{X0 + W}" y="203" as="sourcePoint"/><mxPoint x="{SX}" y="203" as="targetPoint"/></mxGeometry></mxCell>')

# Independent explanation column: not part of the execution path.
GX, GW = 575, 310
box(GX, PY, GW, 24,
    f"rounded=0;html=1;fillColor=#355C7D;strokeColor={LINE};fontSize=12;fontColor=#FFFFFF;fontStyle=1;{FONT}",
    "GuidedMove(s, g)")
text(GX, PY + 27, GW, 25, "Choose a target truck, then evaluate its feasible moves", 10)
widths = (35, 160, 115)
rows = [
    ("Op.", "Target truck", "Move"),
    ("g1", "Last outbound truck on<br>the latest-finishing door", "Relocate"),
    ("g2", "Latest-finishing truck", "Swap destinations"),
    ("g3", "Most tardy truck", "Relocate /<br>swap doors*"),
    ("g4", "Most tardy truck", "Swap destinations"),
]
ty = PY + 57
for ri, row in enumerate(rows):
    height = 24 if ri == 0 else 40
    tx = GX
    for width, value in zip(widths, row):
        box(tx, ty, width, height,
            f"rounded=0;whiteSpace=wrap;html=1;fillColor={'#D9DEE3' if ri == 0 else '#FFFFFF'};"
            f"strokeColor={LINE};fontSize={9 if ri == 0 else 10};fontColor={INK};fontStyle={1 if ri == 0 else 0};{FONT}", value)
        tx += width
    ty += height
text(GX + 5, ty + 8, GW - 10, 55,
     "* g3: outbound → relocate to a feasible door/position;<br>compound → swap doors with another compound truck<br>or move to an unoccupied door.", 10, "left")
box(GX, ty + 70, GW, 34,
    f"rounded=0;html=1;fillColor=#D9DEE3;strokeColor={LINE};fontSize=10;fontColor={INK};{FONT}",
    "No tardy truck: g3 → g1; g4 → g2")
step(GX + 20, ty + 126, GW - 40, 34, "Evaluate all feasible candidate moves")
arrow([(GX + GW / 2, ty + 160), (GX + GW / 2, ty + 180)])
step(GX + 20, ty + 180, GW - 40, 46,
     "Return the best improving solution;<br>otherwise, return the current solution s")
cells.append(f'<mxCell id="{nid()}" parent="1" edge="1" style="endArrow=none;html=1;strokeColor={LINE};dashed=1;dashPattern=3 3;">'
             f'<mxGeometry relative="1" as="geometry"><mxPoint x="{SX + SW}" y="227" as="sourcePoint"/>'
             f'<mxPoint x="{GX}" y="227" as="targetPoint"/></mxGeometry></mxCell>')
decision(CX, 274, f"New best?{small(J(sp) + ' &lt; ' + J(sb))}")
step(SX, 256, SW, 40, f"{sp} ← Descent({sp});<br>{sb} ← {sp};&nbsp; <i>c</i> ← 0{ln('8–9')}", shaded=True)
step(CX - 62, 322, 124, 26, f"<i>c</i> ← <i>c</i> + 1{ln('11')}")

decision(CX, 406, f"Accept candidate?{small(J(sp) + ' &lt; ' + J(s))}")
step(SX, 389, SW, 34, f"{s} ← {sp}{ln('14')}")

decision(CX, 496, f"Stagnation limit reached?{small('<i>c</i> ≥ <i>P</i>')}")
step(SX, 470, SW, 52, "<b>Kick restart</b><br>Start from the best solution<br>Apply K random generic moves<br>Reset stagnation counter", fill="#4E8D8C")

decision(CX, 578, f"Iteration limit reached?{small('<i>n</i> = <i>N</i>')}", h=56)

step(X0, 636, W, 34, f"{sb} ← Descent({sb}){ln('24')}", shaded=True)
terminal(CX, 692, f"Return {sb}")

# ---------------- main flow
arrow([(CX, 32), (CX, 58)])
arrow([(CX, 92), (CX, 108)])
arrow([(CX, 142), (CX, 182)])
arrow([(CX, 224), (CX, 243)])
arrow([(CX, 305), (CX, 322)])
arrow([(CX, 348), (CX, 375)])
arrow([(CX, 437), (CX, 465)])
arrow([(CX, 527), (CX, 550)])
arrow([(CX, 606), (CX, 636)])
arrow([(CX, 670), (CX, 692)])

# ---------------- yes-branches and merges
arrow([(CX + 98, 274), (SX, 274)])
arrow([(SCX, 296), (SCX, 362), (CX, 362)])
arrow([(CX + 98, 406), (SX, 406)])
arrow([(SCX, 423), (SCX, 451), (CX, 451)])
arrow([(CX + 98, 496), (SX, 496)])
arrow([(SCX, 522), (SCX, 539), (CX, 539)])

# ---------------- loop back
arrow([(CX - 98, 578), (LOOPX, 578), (LOOPX, 414)])
step(LOOPX - 30, 386, 60, 28, "<i>n</i> ← <i>n</i> + 1")
arrow([(LOOPX, 386), (LOOPX, 203), (X0, 203)])

# ---------------- branch labels
for y in (274, 406, 496):
    text(CX + 100, y - 16, 30, 14, "yes", 9, "center", GREY)
for y in (305, 437, 527):
    text(CX - 30, y - 2, 24, 14, "no", 9, "right", GREY)
text(CX - 36, 620, 30, 14, "yes", 9, "right", GREY)
text(LOOPX + 4, 562, 60, 14, "no", 9, "left", GREY)

# ---------------- legend
ly = 730
box(10, ly - 8, 540, 2, "line;strokeColor=#CCCCCC;strokeWidth=1;html=1;")
box(10, ly + 3, 22, 14, f"rounded=0;html=1;fillColor={SHADE};strokeColor={INK};")
text(38, ly, 100, 20, "Descent", 9.5, "left")
box(130, ly + 3, 22, 14, "rounded=0;html=1;fillColor=#4E8D8C;strokeColor=#4D4D4D;")
text(158, ly, 90, 20, "Kick restart", 9.5, "left")
box(262, ly + 3, 22, 14, f"rounded=0;html=1;fillColor={ACCL};strokeColor={ACC};strokeWidth=2;")
text(290, ly, 140, 20, "Guided operators", 9.5, "left")
text(10, ly + 24, 540, 20, "<i>s</i>: current solution;  <i>s</i>*: best solution;  <i>c</i>: iterations since the last best update", 9, "left", GREY)

xml = ('<mxfile host="app.diagrams.net"><diagram name="fig_algorithm_flow" id="faf">'
       '<mxGraphModel dx="1000" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
       'fold="1" page="1" pageScale="1" pageWidth="900" pageHeight="790" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w", encoding="utf-8").write(xml)
print("cells", len(cells))
