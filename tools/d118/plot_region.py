# usage: plot_region.py BOARD OUT.png x0 y0 x1 y1 LAYERS(comma: F,In2,In3,B) [px_per_mm] [hilite_nets(comma)]
import os
import sys, pcbnew
from PIL import Image, ImageDraw, ImageFont
bp, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(float, sys.argv[3:7])
lays = sys.argv[7].split(',')
S = float(sys.argv[8]) if len(sys.argv) > 8 else 20
hil = set(sys.argv[9].split(',')) if len(sys.argv) > 9 and sys.argv[9] else set()
b = pcbnew.LoadBoard(bp)
O = 100.0
W, H = int((x1 - x0) * S), int((y1 - y0) * S)
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
f = ImageFont.load_default(size=max(10, int(S * 0.55)))
P = lambda x, y: ((x - O - x0) * S, (y - O - y0) * S)
mm = pcbnew.ToMM
col = {'F.Cu': (220, 40, 40), 'In2.Cu': (40, 160, 40), 'In3.Cu': (40, 80, 220), 'B.Cu': (200, 140, 0)}
names = {'F': 'F.Cu', 'In2': 'In2.Cu', 'In3': 'In3.Cu', 'B': 'B.Cu'}
want = {names[l] for l in lays}
# grid every 5 mm
for gx in range(int(x0) // 5 * 5, int(x1) + 1, 5):
    d.line([P(O + gx, O + y0), P(O + gx, O + y1)], fill=(235, 235, 235)); d.text(P(O + gx + 0.1, O + y0 + 0.1), str(gx), fill=(150, 150, 150), font=f)
for gy in range(int(y0) // 5 * 5, int(y1) + 1, 5):
    d.line([P(O + x0, O + gy), P(O + x1, O + gy)], fill=(235, 235, 235)); d.text(P(O + x0 + 0.1, O + gy + 0.1), str(gy), fill=(150, 150, 150), font=f)
for t in b.GetTracks():
    L = b.GetLayerName(t.GetLayer())
    net = t.GetNetname().split('/')[-1]
    if t.GetClass() == 'PCB_TRACK' and L in want:
        c = col[L] if not hil or net in hil else tuple(int(v * 0.25 + 190) for v in col[L])
        w = max(1, int(mm(t.GetWidth()) * S))
        d.line([P(mm(t.GetStart().x), mm(t.GetStart().y)), P(mm(t.GetEnd().x), mm(t.GetEnd().y))], fill=c, width=w)
    elif t.GetClass() == 'PCB_VIA':
        x, y = mm(t.GetPosition().x), mm(t.GetPosition().y); r = mm(t.GetWidth(pcbnew.F_Cu)) / 2 * S
        a, bb = P(x, y)
        c = (0, 0, 0) if not hil or net in hil else (190, 190, 190)
        d.ellipse([a - r, bb - r, a + r, bb + r], outline=c)
for fp in b.GetFootprints():
    side = 'B' if fp.IsFlipped() else 'F'
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    if cy.OutlineCount():
        bb = cy.BBox()
    else:
        bb = fp.GetBoundingBox(False)
    ax, ay = P(mm(bb.GetX()), mm(bb.GetY())); bx, by = P(mm(bb.GetRight()), mm(bb.GetBottom()))
    if bx < 0 or by < 0 or ax > W or ay > H:
        continue
    oc = (0, 0, 0) if side == 'F' else (160, 0, 160)
    if side == 'F' or 'B' in lays:
        d.rectangle([ax, ay, bx, by], outline=oc)
        d.text((ax + 2, ay + 1), fp.GetReference(), fill=oc, font=f)
    if side == 'F' and ('F' in lays):
        for p in fp.Pads():
            r = p.GetBoundingBox(); px0, py0 = P(mm(r.GetX()), mm(r.GetY())); px1, py1 = P(mm(r.GetRight()), mm(r.GetBottom()))
            d.rectangle([px0, py0, px1, py1], outline=(120, 120, 120))
im.save(out)
print(out, W, H)
