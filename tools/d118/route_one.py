#!/usr/bin/env python3
"""route one open connection as a single 0.1 mm trace on a finished board: other copper fixed, each net kept at its
net class clearance (+ CLR mm, default 0.005), the finished pours as hulls (they refill round the new copper). The
board is filled and saved to OUT; check it with DRC.
START_VIA=x,y (board mm): a via there first, joined to the start pad, and the route from it on any layer (D120:
KBD_BOOT_N, whose pin J1001.12 was boxed in on the top layer, got its via in the pad's free end).
usage: route_one.py IN OUT NET REF.PAD REF.PAD [CLR] [MARGIN]"""
import os, sys
import pcbnew
sys.path.insert(0, os.environ.get('GEN', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen')))
import proute as R
import route_pairs as RP
src, out, net, pa, pz = sys.argv[1:6]
clr = float(sys.argv[6]) if len(sys.argv) > 6 else 0.005      # margin over the net class clearances
margin = float(sys.argv[7]) if len(sys.argv) > 7 else 4.0
b = pcbnew.LoadBoard(src)
full = [n.GetNetname() for n in b.GetNetInfo().NetsByName().values() if n.GetNetname() == net or n.GetNetname().endswith('/' + net)][0]
code = b.FindNet(full).GetNetCode()
ends = []
for rp in (pa, pz):
    fp, p = RP.pad_of(b, rp)
    x, y = R.to_mm(p.GetPosition())
    ends.append((x, y, RP.pad_layer(fp)))
a, z = ends
xs, ys = [a[0], z[0]], [a[1], z[1]]
win = R.Window(min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin, 0.025)
import json
_p = json.load(open(os.path.splitext(src)[0] + '.kicad_pro'))['net_settings']
CL = {c['name']: c['clearance'] for c in _p['classes']}
NC = {k: v[0] for k, v in _p.get('netclass_assignments', {}).items()}
own_clr = CL.get(NC.get(full, 'Default'), 0.1)
net_clr = {n.GetNetCode(): max(own_clr, CL.get(NC.get(n.GetNetname(), 'Default'), 0.1)) + clr
           for n in b.GetNetInfo().NetsByName().values() if n.GetNetCode() > 0}
sv = os.environ.get('START_VIA')
if sv:      # a via beside / in the start pad first, the route starts from it on any layer
    vx, vy = (float(v) - 100 for v in sv.split(','))
    R.add_track(b, full, a[2], [(a[0], a[1]), (vx, vy)], 0.1)
    R.add_via(b, full, vx, vy, RP.VIA[0], RP.VIA[1])
    a = (vx, vy, a[2])
obs = R.Obstacles(b, win, {code}, 0.05, own_clr + clr, via_r=RP.VIA[0] / 2, zones='hull', net_clr=net_clr)
for L in R.ROUTE_LAYERS:
    obs.clear_disk(L, a[0], a[1], 0.0); obs.clear_disk(L, z[0], z[1], 0.0)
cost = {L: 1.0 for L in R.ROUTE_LAYERS}
starts = [(a[0], a[1], L, None) for L in R.ROUTE_LAYERS] if sv else [(a[0], a[1], a[2], None)]
path = R.astar(obs, starts, [(z[0], z[1], z[2], None)], cost, via_cost=0.6 / 0.025, turn_cost=0.2,
               max_expand=20_000_000)
if path is None:
    print('no path'); sys.exit(1)
runs = R.simplify(path)
n = 0
for k, (L, pts) in enumerate(runs):
    pts = list(pts)
    if k == 0: pts[0] = (a[0], a[1])
    if k == len(runs) - 1: pts[-1] = (z[0], z[1])
    R.add_track(b, full, L, pts, 0.1)
    print(L, [(round(x + 100, 3), round(y + 100, 3)) for x, y in pts])
    if k < len(runs) - 1:
        R.add_via(b, full, pts[-1][0], pts[-1][1], RP.VIA[0], RP.VIA[1]); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(out, b)
print(f'{full}: routed, {len(runs)} runs, {n} vias; saved {out}')
