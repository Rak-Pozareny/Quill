#!/usr/bin/env python3
"""where does a GND via (0.4 mm) fit around a pad, as the router's obstacle map sees it (GND's own copper is not an
obstacle; the finished pours are taken as hulls)? Prints a map around each pad, x across, y down, 0.05 mm steps:
'.' a via fits, '#' it does not, 'P' the pad centre. usage: gnd_probe.py BOARD REF.PAD [REF.PAD ...]"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R  # noqa: E402
import route_pairs as RP  # noqa: E402

b = pcbnew.LoadBoard(sys.argv[1])
gnd = b.FindNet('GND').GetNetCode()
for arg in sys.argv[2:]:
    ref, num = arg.split('.')
    pad = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
    cx, cy = R.to_mm(pad.GetPosition())
    r = 2.0
    win = R.Window(cx - r - 0.5, cy - r - 0.5, cx + r + 0.5, cy + r + 0.5, 0.05)
    obs = R.Obstacles(b, win, {gnd}, 0.05, 0.12, via_r=RP.VIA[0] / 2, zones='hull')
    print(f'{arg} at ({cx:.2f}, {cy:.2f}); columns x {cx - r:.2f} .. {cx + r:.2f}')
    y = cy - r
    while y <= cy + r + 1e-9:
        line, x = '', cx - r
        while x <= cx + r + 1e-9:
            if abs(x - cx) < 0.026 and abs(y - cy) < 0.026:
                line += 'P'
            else:
                line += '.' if obs.via_free(*win.ij(x, y)) else '#'
            x += 0.05
        print(f'  y {y:6.2f} {line}')
        y += 0.1
