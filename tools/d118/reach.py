#!/usr/bin/env python3
"""how far a 0.1 mm trace of NET can get from a pad (flood fill over F / In2 / In3 / B with vias), finished pours as
hulls. usage: reach.py BOARD NET REF.PAD [CLR] [R]"""
import os, sys
from collections import deque
import pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R
import route_pairs as RP
bp, net, pa = sys.argv[1:4]
clr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.12
rad = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
b = pcbnew.LoadBoard(bp)
full = [n.GetNetname() for n in b.GetNetInfo().NetsByName().values() if n.GetNetname() == net or n.GetNetname().endswith('/' + net)][0]
code = b.FindNet(full).GetNetCode()
fp, p = RP.pad_of(b, pa)
x, y = R.to_mm(p.GetPosition()); L0 = RP.pad_layer(fp)
win = R.Window(x - rad, y - rad, x + rad, y + rad, 0.025)
obs = R.Obstacles(b, win, {code}, 0.05, clr, via_r=RP.VIA[0] / 2, zones='hull')
for L in R.ROUTE_LAYERS:
    obs.clear_disk(L, x, y, 0.0)
i0, j0 = win.ij(x, y)
seen = {(i0, j0, L0)}; q = deque([(i0, j0, L0)])
while q:
    i, j, L = q.popleft()
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        n = (i + di, j + dj, L)
        if n not in seen and obs.free(L, n[0], n[1]):
            seen.add(n); q.append(n)
    if obs.via_free(i, j):
        for L2 in R.ROUTE_LAYERS:
            if L2 != L and (i, j, L2) not in seen and obs.free(L2, i, j):
                seen.add((i, j, L2)); q.append((i, j, L2))
by = {}
for i, j, L in seen:
    by.setdefault(L, []).append((i, j))
print(f'{pa} ({x + 100:.2f}, {y + 100:.2f}) on {L0}: {len(seen)} cells reachable')
for L, c in by.items():
    xs = [win.x0 + i * win.res + 100 for i, _ in c]; ys = [win.y0 + j * win.res + 100 for _, j in c]
    print(f'  {L}: {len(c)} cells, x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}')
