"""Timeline of the inter-door transfer example (R2-3).

Numbers follow docs/revision_drafts/R2-3_interdoor_transfer_time.md:
source A at door (30, 40) -> t = 5, unloading ends 20, sends 10 units;
source B at door (0, 20)  -> t = 2, unloading ends 26, sends 4 units;
receiver at door (0, 0): own unloading ends 24, loading 14, leaving 1.

    python3 make_fig_transfer_timeline.py fig_transfer_timeline.drawio
"""
import sys
from xml.sax.saxutils import escape

INK, GREY, LINE = "#222222", "#666666", "#333333"
C_UNLOAD, C_TRANSFER, C_LOAD, C_LEAVE = "#D9D9D9", "#2F5D8A", "#3A9E7E", "#8C8C8C"
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


def text(x, y, w, h, value, size=10, align="center", color=INK, bold=False, valign="middle"):
    box(x, y, w, h,
        f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign={valign};"
        f"whiteSpace=wrap;fontSize={size};fontColor={color};fontStyle={1 if bold else 0};{FONT}", value)


def line(pts, arrow=False, dashed=False, color=LINE, width=1.2):
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts[1:-1])
    st = ("endArrow=block;endFill=1;endSize=5;" if arrow else "endArrow=none;") + \
         f"html=1;rounded=0;strokeColor={color};strokeWidth={width};" + ("dashed=1;dashPattern=4 3;" if dashed else "")
    cells.append(
        f'<mxCell id="{nid()}" parent="1" edge="1" style="{st}"><mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/>'
        f'<Array as="points">{mid}</Array></mxGeometry></mxCell>'
    )


T0, T1, S, X0 = 14, 44, 16, 176      # first/last time, px per time unit, x of T0
BH = 26                              # bar height


def X(t):
    return X0 + (t - T0) * S


def bar(t_from, t_to, y, fill, label="", font="#FFFFFF", dashed=False, stroke=INK):
    dash = "dashed=1;dashPattern=3 2;" if dashed else ""
    box(X(t_from), y, (t_to - t_from) * S, BH,
        f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1.2;{dash}"
        f"fontSize=9.5;fontColor={font};{FONT}", label)


def row_label(y, title, sub):
    text(8, y - 4, 160, BH + 8,
         f"<b>{title}</b><br><span style='font-size:8.5px;color:{GREY}'>{sub}</span>", 10, "left")


Y_B, Y_A, Y_R = 52, 112, 184

text(8, 6, 660, 18, "Inter-door transfer and loading: a numerical example", 12, "left", bold=True)

# ---------------- source truck B
row_label(Y_B, "Source truck B", "door at (0, 20); sends 4 units")
bar(T0, 26, Y_B, C_UNLOAD, "unloading", INK)
bar(26, 28, Y_B, C_TRANSFER)
text(X(26) - 60, Y_B - 17, 152, 14, "transfer <i>t</i> = 20/10 = 2", 9, "center", C_TRANSFER)

# ---------------- source truck A
row_label(Y_A, "Source truck A", "door at (30, 40); sends 10 units")
bar(T0, 20, Y_A, C_UNLOAD, "unloading", INK)
bar(20, 25, Y_A, C_TRANSFER, "transfer")
text(X(20) - 36, Y_A - 17, 152, 14, "<i>t</i> = 50/10 = 5 (not 10 × 5)", 9, "center", C_TRANSFER)

# ---------------- receiving compound truck
row_label(Y_R, "Receiving compound truck", "door at (0, 0); own unloading ends at 24")
bar(T0, 24, Y_R, C_UNLOAD, "unloading", INK)
bar(24, 28, Y_R, "#FFFFFF", "waiting", GREY, dashed=True, stroke="#888888")
bar(28, 42, Y_R, C_LOAD, "loading (10 + 4) × 1 = 14")
bar(42, 43, Y_R, C_LEAVE)
text(X(43) + 4, Y_R, 40, BH, "leaves<br>at 43", 9, "left", GREY)

# ---------------- freight arrivals at the receiving door
line([(X(28), Y_B + BH), (X(28), Y_R)], arrow=True, color=C_TRANSFER, width=1.5)
line([(X(25), Y_A + BH), (X(25), Y_R)], arrow=True, color=C_TRANSFER, width=1.5)
text(X(28) + 5, Y_B + BH + 4, 110, 14, "freight arrives at 28", 9, "left", C_TRANSFER)
text(X(25) - 114, Y_A + BH + 6, 110, 14, "freight arrives at 25", 9, "right", C_TRANSFER)

# ---------------- ready time
line([(X(28), Y_R + BH), (X(28), Y_R + BH + 26)], dashed=True, color=INK)
text(X(28) - 150, Y_R + BH + 24, 300, 14, "freight ready = max(25, 28) = 28;&nbsp; loading starts at max(24, 28) = 28", 9, "center")

# ---------------- time axis
AY = 266
line([(X(T0), AY), (X(T1) + 8, AY)], arrow=True)
for t in range(T0, T1 + 1, 2):
    line([(X(t), AY), (X(t), AY + 4)])
    text(X(t) - 14, AY + 5, 28, 12, str(t), 8.5, "center", GREY)
for t in (25, 43):
    line([(X(t), AY), (X(t), AY + 4)])
text(X(T1) - 20, AY - 16, 50, 12, "time", 9, "right", GREY)

# ---------------- legend
ly = 296
box(8, ly - 6, 660, 2, "line;strokeColor=#CCCCCC;strokeWidth=1;html=1;")
x = 8
for fill, lab, w, dashed in ((C_UNLOAD, "unloading", 74, False), (C_TRANSFER, "inter-door transfer (door pair only)", 196, False),
                             ("#FFFFFF", "waiting", 62, True), (C_LOAD, "loading (quantity × unit time)", 166, False),
                             (C_LEAVE, "leaving", 60, False)):
    dash = "dashed=1;dashPattern=3 2;" if dashed else ""
    box(x, ly + 4, 18, 12, f"rounded=0;html=1;fillColor={fill};strokeColor={INK};{dash}")
    text(x + 23, ly, w, 20, lab, 9.5, "left")
    x += 23 + w + 8

xml = ('<mxfile host="app.diagrams.net"><diagram name="fig_transfer_timeline" id="ftt">'
       '<mxGraphModel dx="1000" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
       'fold="1" page="1" pageScale="1" pageWidth="680" pageHeight="322" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + '</root></mxGraphModel></diagram></mxfile>')
open(sys.argv[1], "w", encoding="utf-8").write(xml)
print("cells", len(cells))
