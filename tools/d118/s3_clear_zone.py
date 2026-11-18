#!/usr/bin/env python3
"""remove copper of every net inside a box on all layers, except the listed nets and DSI; GND included (locked or
not); other locked items kept. usage: clear_zone.py BOARD x0 y0 x1 y1 KEEP,NETS"""
import os
import sys, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import proute as R
path = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6]); keep = set(sys.argv[6].split(','))
b = pcbnew.LoadBoard(path); mm = pcbnew.ToMM
n = 0; nets = set()
for t in list(R.tracks(b)):
    net = t.GetNetname().split('/')[-1]
    if net in keep or net.startswith('DSI_') or (t.IsLocked() and net != 'GND'):
        continue
    pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
    xs = [mm(q.x) - 100 for q in pts]; ys = [mm(q.y) - 100 for q in pts]
    if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
        continue
    R.remove(b, t); n += 1; nets.add(net)
pcbnew.SaveBoard(path, b)
print(f'zone ({x0},{y0})-({x1},{y1}): removed {n} items of {", ".join(sorted(nets))}')
