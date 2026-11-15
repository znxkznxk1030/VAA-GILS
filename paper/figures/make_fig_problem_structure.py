import sys
from xml.sax.saxutils import escape
C = {"d1": "#2F5D8A", "d2": "#7B5EA7", "d3": "#3A9E7E"}
L = {"d1": "#C9D8EA", "d2": "#DDD3EC", "d3": "#C5E6DA"}
INK, GREY = "#222222", "#666666"
cells, n = [], [0]
def nid():
    n[0] += 1; return f"c{n[0]}"
def box(x, y, w, h, style, value=""):
    cells.append(f'<mxCell id="{nid()}" parent="1" vertex="1" style="{style}" value="{escape(value, {chr(34): "&quot;"})}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
def text(x, y, w, h, value, size=11, align="center", color=INK, bold=False, valign="middle"):
    st = f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign={valign};whiteSpace=wrap;fontSize={size};fontColor={color};fontFamily=Helvetica;fontStyle={1 if bold else 0};"
    box(x, y, w, h, st, value)
def arrow(pts, color, dashed=False, width=2):
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
    st = f"endArrow=block;endFill=1;endSize=5;html=1;rounded=0;strokeColor={color};strokeWidth={width};" + ("dashed=1;dashPattern=4 3;" if dashed else "")
    cells.append(f'<mxCell id="{nid()}" parent="1" edge="1" style="{st}"><mxGeometry relative="1" as="geometry"><mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/><Array as="points">{mid}</Array></mxGeometry></mxCell>')
def sub(sym, s): return f"<i>{sym}</i><sub>{s}</sub>"
def dest(k): return sub("d", k[1])
def block(x, y, w, h, k, kept, label=None):
    if kept:
        st = f"rounded=0;html=1;fillColor={C[k]};strokeColor={INK};strokeWidth=1.5;fontColor=#FFFFFF;fontSize=11;fontStyle=1;fontFamily=Helvetica;"
    else:
        st = f"rounded=0;html=1;fillColor={L[k]};strokeColor={C[k]};dashed=1;dashPattern=3 2;fontColor={INK};fontSize=11;fontFamily=Helvetica;"
    box(x, y, w, h, st, label if label is not None else dest(k))
TRUCK = f"rounded=0;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=1.3;"
DOCK = "rounded=0;html=1;fillColor=#F1F1F1;strokeColor=#444444;strokeWidth=2;"
ROOF = "rounded=0;html=1;fillColor=#555555;strokeColor=#444444;strokeWidth=2;fontColor=#FFFFFF;fontSize=10;fontStyle=1;fontFamily=Helvetica;"
def dock(x, w):
    box(x, 32, w, 108, DOCK)
    box(x, 32, w, 16, ROOF, "Cross-dock")
TW, TH, TY = 50, 112, 158   # trailer width, trailer length, top y (rear end at the door)
WHEEL = "rounded=0;html=1;fillColor=#333333;strokeColor=#333333;"
CAB = f"rounded=0;html=1;fillColor=#D9D9D9;strokeColor={INK};strokeWidth=1.3;"
def truck(cx, dashed=False):
    x = cx - TW / 2
    dash = "dashed=1;dashPattern=5 3;" if dashed else ""
    for wy in (TY + 12, TY + TH - 34):
        for wx in (x - 6, x + TW):
            box(wx, wy, 6, 20, WHEEL)
    for wx in (cx - 17 - 5, cx + 17):
        box(wx, TY + TH + 5, 5, 12, WHEEL)
    box(cx - 17, TY + TH, 34, 20, CAB + dash)
    box(x, TY, TW, TH, TRUCK + dash)
def load(cx, items):
    y = TY + 8
    for k, kept, h, label in items:
        block(cx - 19, y, 38, h, k, kept, label)
        y += h + 4
def kept_label(k): return f"{dest(k)}<br><span style='font-size:8px'>kept</span>"
LABEL_Y = TY + TH + 22
DOOR = f"rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#888888;fontSize=9;fontColor={GREY};fontFamily=Helvetica;"

# ---------------- panel (a)
text(10, 6, 370, 20, "(a) Conventional cross-docking", 12, "left", bold=True)
dock(20, 352)
ax = {"I1": 62, "I2": 148, "O1": 244, "O2": 330}
for name, cx in ax.items():
    box(cx - 32, 132, 64, 14, DOOR, "inbound" if name[0] == "I" else "outbound")
    truck(cx)
for name in ("I1", "I2"):
    cx = ax[name]
    load(cx, [("d1", False, 46, None), ("d2", False, 46, None)])
    text(cx - 40, LABEL_Y, 80, 18, f"inbound {sub('I', name[1])}", 11)
load(ax["O1"], [("d1", True, 96, None)])
load(ax["O2"], [("d2", True, 96, None)])
text(ax["O1"] - 40, LABEL_Y, 80, 18, f"outbound {sub('O', '1')}", 11)
text(ax["O2"] - 40, LABEL_Y, 80, 18, f"outbound {sub('O', '2')}", 11)
arrow([(54, 132), (54, 66), (236, 66), (236, 132)], C["d1"])
arrow([(140, 132), (140, 80), (252, 80), (252, 132)], C["d1"])
arrow([(70, 132), (70, 96), (322, 96), (322, 132)], C["d2"])
arrow([(156, 132), (156, 110), (338, 110), (338, 132)], C["d2"])
text(20, 338, 345, 44, "Inbound trucks unload all freight; a different truck carries each destination's freight out.", 10.5, "left", GREY, valign="top")

# ---------------- panel (b)
X = 400
text(X, 6, 380, 20, "(b) This study: compound trucks", 12, "left", bold=True)
dock(X + 8, 372)
c1, c2, cf = X + 70, X + 215, X + 322
for cx, lab in ((c1, "door 1"), (c2, "door 2")):
    box(cx - 32, 132, 64, 14, DOOR, lab)
    truck(cx)
# compound i1 keeps d1, unloads d2 and d3
load(c1, [("d1", True, 34, kept_label("d1")), ("d2", False, 27, None), ("d3", False, 27, None)])
# compound i2 keeps d2, unloads d1 and d3
load(c2, [("d2", True, 34, kept_label("d2")), ("d1", False, 27, None), ("d3", False, 27, None)])
text(c1 - 55, LABEL_Y, 110, 18, f"compound {sub('i', '1')}", 11)
text(c2 - 55, LABEL_Y, 110, 18, f"compound {sub('i', '2')}", 11)
# outbound f waits for door 2
truck(cf, dashed=True)
load(cf, [("d3", True, 96, None)])
text(cf - 50, LABEL_Y, 100, 18, "outbound <i>f</i>", 11)
arrow([(cf, TY), (cf, 151), (c2 + 52, 151), (c2 + 34, 142)], '#333333', dashed=True, width=1.3)
text(cf - 80, LABEL_Y + 16, 160, 26, f"door is a decision (here door 2);<br>docks after {sub('i', '2')} leaves", 9, "center", GREY)
# transfers
arrow([(c1 - 14, 132), (c1 - 14, 64), (c2 - 14, 64), (c2 - 14, 132)], C["d2"])   # d2: i1 -> i2
arrow([(c2 + 2, 132), (c2 + 2, 84), (c1 + 2, 84), (c1 + 2, 132)], C["d1"])       # d1: i2 -> i1
arrow([(c1 + 18, 132), (c1 + 18, 104), (c2 + 60, 104)], C["d3"])                 # d3: i1 -> staging at door 2
arrow([(c2 + 20, 132), (c2 + 20, 118), (c2 + 60, 118)], C["d3"])                 # d3: i2 -> staging
box(c2 + 60, 94, 98, 34, f"rounded=0;html=1;fillColor={L['d3']};strokeColor={C['d3']};fontSize=9.5;fontColor={INK};fontFamily=Helvetica;", f"{dest('d3')} freight waits<br>for <i>f</i>")
text(c1 + 20, 50, 130, 13, f"inter-door transfer, time {sub('t', 'mn')}", 9, "center", GREY)
ov = '<span style="text-decoration:overline"><i>d</i></span><sub><i>q</i></sub>'
text(X + 8, 338, 372, 56, f"One feasible assignment is shown. A compound truck keeps one destination's freight, unloads the rest, then loads the freight other trucks unloaded for that destination. Each truck <i>q</i> has an arrival time {sub('r', 'q')} and a soft due date {ov}, so a late {sub('i', '2')} delays {sub('i', '1')} and <i>f</i>.", 10.5, "left", GREY, valign="top")

# ---------------- legend
ly = 408
box(20, ly - 8, 760, 2, "line;strokeColor=#CCCCCC;strokeWidth=1;html=1;")
x = 20
for k in ("d1", "d2", "d3"):
    box(x, ly + 6, 14, 14, f"rounded=0;html=1;fillColor={C[k]};strokeColor={INK};")
    text(x + 18, ly + 3, 70, 20, f"destination {dest(k)}", 10, "left"); x += 100
block(x + 10, ly + 5, 22, 16, "d1", True, ""); text(x + 36, ly + 3, 170, 20, "freight on the outbound carrier", 10, "left"); x += 205
block(x + 10, ly + 5, 22, 16, "d1", False, ""); text(x + 36, ly + 3, 90, 20, "unloaded freight", 10, "left"); x += 130
arrow([(x + 10, ly + 13), (x + 40, ly + 13)], '#333333'); text(x + 44, ly + 3, 100, 20, "inter-door transfer", 10, "left")

xml = ('<mxfile host="app.diagrams.net"><diagram name="fig_problem_structure" id="fps">'
       '<mxGraphModel dx="1000" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="800" pageHeight="442" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w", encoding="utf-8").write(xml)
print("cells", len(cells))
