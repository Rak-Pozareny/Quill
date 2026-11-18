#!/usr/bin/env python3
"""copper clearance of a through via (0.4 / 0.2) at candidate spots to every other-net item, all copper layers
(KiCad shapes). usage: via_search.py BOARD X Y SPAN STEP NET [MIN]"""
import sys, math, itertools
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); X, Y, span, step = map(float, sys.argv[2:6]); net = sys.argv[6]
need = float(sys.argv[7]) if len(sys.argv) > 7 else 0.15
code = b.FindNet(net).GetNetCode()
import json, os
_p = json.load(open(os.path.splitext(sys.argv[1])[0] + '.kicad_pro'))['net_settings']
CLR = {c['name']: c['clearance'] for c in _p['classes']}
NC = {k: v[0] for k, v in _p.get('netclass_assignments', {}).items()}
layers = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu]
items = []
for fp in b.GetFootprints():
    items += [p for p in fp.Pads()]
items += [t for t in b.GetTracks()]
near = []
for it in items:
    if it.GetNetCode() == code: continue
    bb = it.GetBoundingBox()
    if bb.GetRight() < pcbnew.FromMM(X - span - 1.5) or bb.GetX() > pcbnew.FromMM(X + span + 1.5) or \
       bb.GetBottom() < pcbnew.FromMM(Y - span - 1.5) or bb.GetY() > pcbnew.FromMM(Y + span + 1.5): continue
    for L in layers:
        if it.IsOnLayer(L):
            ps = pcbnew.SHAPE_POLY_SET(); it.TransformShapeToPolygon(ps, L, 0, 1000, pcbnew.ERROR_OUTSIDE)
            near.append((it, L, ps))
# rule areas that forbid vias (board level and inside footprints, e.g. the U.FL's keepout on the back)
keepouts = []
for z in list(b.Zones()) + [z for fp in b.GetFootprints() for z in fp.Zones()]:
    if z.GetIsRuleArea() and z.GetDoNotAllowVias():
        keepouts.append((z.GetZoneName() or z.GetParentFootprint().GetReference() if z.GetParentFootprint() else z.GetZoneName(),
                         z.Outline().CloneDropTriangulation()))
# own-net via holes and other holes: hole to hole 0.25 (centre distance >= 0.45 for two 0.2 drills)
holes = [(t.GetPosition(), t.GetDrillValue() / 2e6) for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'] + \
        [(p.GetPosition(), p.GetDrillSize().x / 2e6) for fp in b.GetFootprints() for p in fp.Pads() if p.HasHole()]
def check(x, y):
    c = pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))
    worst = (9, None)
    for it, L, sh in near:
        d = 0.0 if sh.Contains(c) else pcbnew.ToMM(sh.SquaredDistance(c, False) ** 0.5)
        req = max(0.1, CLR.get(NC.get(it.GetNetname(), 'Default'), 0.1))
        g = d - 0.2 - req
        if g < worst[0]: worst = (g, f'{it.GetClass()[4:] if hasattr(it, "GetClass") else "PAD"} {it.GetNetname()[-14:]} {b.GetLayerName(L)}')
    hh = min((math.dist((x, y), (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))) - r - 0.1 for p, r in holes
              if math.dist((x, y), (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))) > 0.01), default=9)
    for name, ps in keepouts:
        d = 0.0 if ps.Contains(c) else pcbnew.ToMM(ps.SquaredDistance(c, False) ** 0.5)
        if d - 0.2 < worst[0]: worst = (d - 0.2 - 0.0 if not ps.Contains(c) else -1.0, f'KEEPOUT {name}')
    return worst, hh
w, hh = check(X, Y); print(f'at ({X}, {Y}): copper slack {w[0]:.3f} to {w[1]}; hole-hole {hh:.3f}')
best = []
n = int(round(span / step))
for i, j in itertools.product(range(-n, n + 1), repeat=2):
    x, y = X + i * step, Y + j * step
    w, hh = check(x, y)
    if w[0] >= 0.0 and hh >= 0.2: best.append((math.dist((x, y), (X, Y)), x, y, w, hh))
best.sort()
for d, x, y, w, hh in best[:int(os.environ.get("TOP", "8"))]: print(f'  ({x:.3f}, {y:.3f}) moved {d:.3f}: copper slack {w[0]:.3f} ({w[1]}), hole-hole {hh:.3f}')
print(len(best), 'spots')
