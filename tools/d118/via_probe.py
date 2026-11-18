#!/usr/bin/env python3
"""where can a DSI via (0.4 mm) go in front of J701? For each lane, print free via spots on a 0.05 grid in
x 52.4-54.3, y lane-1.2 .. lane+1.2 as the pair router's obstacle map sees them. usage: via_probe.py BOARD"""
import os
import sys, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as _PR
_ObsInit = _PR.Obstacles.__init__
def _obs_init(self, *a, **k):
    k.setdefault('zones', 'hull')      # a routed board: the finished pours are refilled round new copper (D118)
    _ObsInit(self, *a, **k)
_PR.Obstacles.__init__ = _obs_init
import proute as R, route_pairs as RP
b = pcbnew.LoadBoard(sys.argv[1])
full = {str(n).split('/')[-1]: str(n) for n in R.net_names(b)}
lanes = {'D0': 19.0, 'D1': 20.5, 'CLK': 22.0, 'D2': 23.5, 'D3': 25.0}
win = R.Window(51.0, 16.5, 55.0, 27.0, 0.05)
for lane, yc in lanes.items():
    own = {b.FindNet(full[f'DSI_{lane}_P']).GetNetCode(), b.FindNet(full[f'DSI_{lane}_N']).GetNetCode()}
    obs = R.Obstacles(b, win, own, 0.06, RP.CLR + RP.MARGIN, via_r=RP.VIA[0] / 2, escapes='coarse')
    rows = []
    y = yc - 1.2
    while y <= yc + 1.2 + 1e-9:
        x = 52.4; line = ''
        while x <= 54.3 + 1e-9:
            line += '#' if not obs.via_free(*win.ij(x, y)) else '.'
            x += 0.05
        rows.append(f'  y {y:5.2f} {line}')
        y += 0.1
    print(f'{lane} (pads at y {yc - 0.25:.2f} / {yc + 0.25:.2f}); columns x 52.40 .. 54.30 step 0.05, . = via fits')
    print('\n'.join(rows))
