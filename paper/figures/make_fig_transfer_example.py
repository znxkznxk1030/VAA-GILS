"""How freight moves inside the cross-dock (R2-3): floor plan with a numerical example.

Door coordinates (floor units): carrier door (30, 0), source A door (60, 40), source B door (10, 0).
  A -> carrier: distance 50, t = 50/10 = 5, unloading done at 20, 10 units, arrives at 25
  B -> carrier: distance 20, t = 20/10 = 2, unloading done at 26,  4 units, arrives at 28
  carrier: own unloading done at 24, loads (10 + 4) x 1 = 14 from 28 to 42, leaves at 43

    python3 make_fig_transfer_example.py fig_transfer_example.drawio
"""
import sys
from xml.sax.saxutils import escape

INK, GREY = "#222222", "#666666"
CD, LD = "#2F5D8A", "#C9D8EA"        # destination d: solid (on carrier) / light (unloaded)
KEPT = "#BDBDBD"
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


def text(x, y, w, h, value, size=10, align="center", color=INK, bold=False, valign="middle", italic=False):
    fs = (1 if bold else 0) + (2 if italic else 0)
    box(x, y, w, h,
        f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign={valign};"
        f"whiteSpace=wrap;fontSize={size};fontColor={color};fontStyle={fs};{FONT}", value)


def line(pts, color=CD, width=2.5, dashed=False, arrow=True):
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
    st = (("endArrow=block;endFill=1;endSize=6;" if arrow else "endArrow=none;")
          + f"html=1;rounded=0;strokeColor={color};strokeWidth={width};"
          + ("dashed=1;dashPattern=4 3;" if dashed else ""))
    cells.append(
        f'<mxCell id="{nid()}" parent="1" edge="1" style="{st}"><mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/>'
        f'<Array as="points">{mid}</Array></mxGeometry></mxCell>'
    )


def badge(x, y, num):
    box(x, y, 15, 15,
        f"rounded=0;html=1;fillColor=#333333;strokeColor=#333333;fontSize=9.5;fontColor=#FFFFFF;fontStyle=1;{FONT}",
        str(num))


def small(s):
    return f"<span style='font-size:8.5px;color:{GREY}'>{s}</span>"


# ---------------- floor geometry: 70 x 40 floor units, 6 px per unit
S, OX, TOP = 6, 110, 132
W, H = 70 * S, 40 * S
BOT = TOP + H


def PX(x):
    return OX + x * S


def PY(y):
    return BOT - y * S


A, R, B = (60, 40), (30, 0), (10, 0)

text(10, 4, 580, 20, "Inter-door transfer of the freight for one destination <i>d</i>", 12, "left", bold=True)

# floor
box(OX, TOP, W, H, "rounded=0;html=1;fillColor=#F4F4F4;strokeColor=#444444;strokeWidth=2.5;")
text(OX + 6, TOP + 4, 120, 14, "Cross-dock floor", 9.5, "left", GREY, bold=True)
text(OX - 44, BOT - 6, 42, 12, "(0, 0)", 8.5, "right", GREY)
text(OX + W - 20, TOP - 21, 48, 12, "(70, 40)", 8.5, "left", GREY)

# ---------------- trucks (trailer rear at the door)
TW, TH = 40, 72
TRUCK = f"rounded=0;html=1;fillColor=#FFFFFF;strokeColor={INK};strokeWidth=1.3;"
WHEEL = "rounded=0;html=1;fillColor=#333333;strokeColor=#333333;"
CAB = f"rounded=0;html=1;fillColor=#D9D9D9;strokeColor={INK};strokeWidth=1.3;"
DOOR = f"rounded=0;html=1;fillColor=#FFFFFF;strokeColor=#666666;strokeWidth=1.2;fontSize=8.5;fontColor={INK};{FONT}"


def truck(cx, below):
    """Truck docked at the bottom wall (below=True) or the top wall (below=False)."""
    x = cx - TW / 2
    ty = BOT + 10 if below else TOP - 10 - TH
    for wy in (ty + 8, ty + TH - 24):
        for wx in (x - 5, x + TW):
            box(wx, wy, 5, 16, WHEEL)
    cab_y = ty + TH if below else ty - 16
    for wx in (cx - 14 - 4, cx + 14):
        box(wx, cab_y + 3, 4, 10, WHEEL)
    box(cx - 14, cab_y, 28, 16, CAB)
    box(x, ty, TW, TH, TRUCK)
    return ty


def block(cx, y, h, kind, label):
    if kind == "carried":
        st = f"rounded=0;html=1;fillColor={CD};strokeColor={INK};strokeWidth=1.5;fontColor=#FFFFFF;fontSize=9.5;fontStyle=1;{FONT}"
    elif kind == "unloaded":
        st = f"rounded=0;html=1;fillColor={LD};strokeColor={CD};dashed=1;dashPattern=3 2;fontColor={INK};fontSize=9;{FONT}"
    else:
        st = f"rounded=0;html=1;fillColor={KEPT};strokeColor={INK};fontColor={INK};fontSize=8.5;{FONT}"
    box(cx - 15, y, 30, h, st, label)


# source truck A at the top wall: freight for d sits at the rear (door side, bottom of the trailer)
ty = truck(PX(A[0]), below=False)
block(PX(A[0]), ty + 6, 30, "kept", "kept")
block(PX(A[0]), ty + 40, 26, "unloaded", "<i>d</i>: 10")
# source truck B and the carrier at the bottom wall (door side is the top of the trailer)
ty = truck(PX(B[0]), below=True)
block(PX(B[0]), ty + 6, 26, "unloaded", "<i>d</i>: 4")
block(PX(B[0]), ty + 36, 30, "kept", "kept")
ty = truck(PX(R[0]), below=True)
block(PX(R[0]), ty + 6, 60, "carried", "<i>d</i><br><span style='font-size:8px'>kept</span>")

# doors
for (x, y), lab in ((A, "door (60, 40)"), (R, "door (30, 0)"), (B, "door (10, 0)")):
    box(PX(x) - 36, PY(y) - 7, 72, 14, DOOR, lab)

# truck labels
text(PX(A[0]) - 190, TOP - 96, 160, 30, "<b>source truck A</b>", 10, "right")
text(PX(B[0]) - 76, BOT + 100, 152, 16, "<b>source truck B</b>", 10)
text(PX(R[0]) - 90, BOT + 100, 180, 16, "<b>carrier of <i>d</i></b> (compound truck)", 10)

# ---------------- freight in front of the doors
STG = f"rounded=0;html=1;fillColor={LD};strokeColor={CD};dashed=1;dashPattern=3 2;fontSize=9;fontColor={INK};{FONT}"
box(PX(A[0]) + 8, TOP + 12, 48, 26, STG, "10 units")
box(PX(B[0]) - 30, BOT - 38, 58, 26, STG, "4 units")
box(PX(R[0]) - 22, BOT - 40, 86, 28,
    f"rounded=0;html=1;fillColor={LD};strokeColor={CD};strokeWidth=1.5;fontSize=9;fontColor={INK};{FONT}",
    "freight for <i>d</i><br>waits for loading")

# ---------------- direct transfers (straight door-to-door moves)
# A -> carrier: the true straight line between the two doors, trimmed at both ends
ax, ay, rx, ry = PX(A[0]), PY(A[1]), PX(R[0]), PY(R[1])
ux, uy = (rx - ax) / 300.0, (ry - ay) / 300.0
line([(ax + ux * 20, ay + uy * 20), (ax + ux * 252, ay + uy * 252)])
# B -> carrier along the floor
line([(PX(B[0]) + 30, BOT - 25), (PX(R[0]) - 24, BOT - 25)])

# distance legs for A -> carrier
line([(ax, TOP + 44), (ax, BOT - 8)], color="#999999", width=1, dashed=True, arrow=False)
line([(ax, BOT - 8), (rx + 70, BOT - 8)], color="#999999", width=1, dashed=True, arrow=False)
text(ax + 4, TOP + 150, 30, 14, "40", 9, "left", GREY)
text(rx + 110, BOT - 24, 30, 14, "30", 9, "center", GREY)

# transfer labels
text(ax - 330, TOP + 90, 212, 30,
     "distance √(30² + 40²) = 50<br><b>transfer time = 50/10 = 5</b>", 9.5, "right", CD)
text(PX(B[0]) - 8, BOT - 84, 200, 30,
     "distance 20<br><b>transfer time = 20/10 = 2</b>", 9.5, "left", CD)

text(OX + 8, TOP + 26, 190, 40,
     "Direct transfer: freight goes straight from the source door to the carrier's door. "
     "The transfer time is the door distance divided by 10.", 9, "left", GREY, italic=True, valign="top")

# ---------------- legend
ly = BOT + 132
box(10, ly - 6, 580, 2, "line;strokeColor=#CCCCCC;strokeWidth=1;html=1;")
box(10, ly + 4, 20, 13, f"rounded=0;html=1;fillColor={LD};strokeColor={CD};dashed=1;dashPattern=3 2;")
text(35, ly, 130, 20, "freight for <i>d</i>, unloaded", 9.5, "left")
box(175, ly + 4, 20, 13, f"rounded=0;html=1;fillColor={CD};strokeColor={INK};")
text(200, ly, 150, 20, "freight for <i>d</i> on its carrier", 9.5, "left")
line([(365, ly + 10), (395, ly + 10)])
text(401, ly, 180, 20, "direct inter-door transfer", 9.5, "left")
box(10, ly + 26, 20, 13, f"rounded=0;html=1;fillColor={KEPT};strokeColor={INK};")
text(35, ly + 22, 300, 20, "freight a source truck keeps for another destination", 9.5, "left")

xml = ('<mxfile host="app.diagrams.net"><diagram name="fig_transfer_example" id="fte">'
       f'<mxGraphModel dx="1000" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
       f'fold="1" page="1" pageScale="1" pageWidth="600" pageHeight="{ly + 50}" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w", encoding="utf-8").write(xml)
print("cells", len(cells))
