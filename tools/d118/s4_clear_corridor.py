#!/usr/bin/env python3
"""remove unlocked (router) single-ended copper on In2 / In3 and unlocked vias inside a box, keep the listed nets;
then dangling copper. usage: clear_corridor.py IN OUT x0 y0 x1 y1 [KEEP,NETS]"""
import os
import sys, pcbnew
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'gen'))
import gndfix, proute as R
src, out = sys.argv[1:3]
x0, y0, x1, y1 = map(float, sys.argv[3:7])
keep = set(sys.argv[7].split(',')) if len(sys.argv) > 7 else set()
b = pcbnew.LoadBoard(src)
mm = pcbnew.ToMM
n = 0
nets = set()
for t in list(R.tracks(b)):
    net = t.GetNetname().split('/')[-1]
    if t.IsLocked() or net in keep or net == 'GND':
        continue
    if t.GetClass() == 'PCB_VIA':
        x, y = mm(t.GetPosition().x) - 100, mm(t.GetPosition().y) - 100
        inside = x0 <= x <= x1 and y0 <= y <= y1
    else:
        if b.GetLayerName(t.GetLayer()) not in ('In2.Cu', 'In3.Cu'):
            continue
        xs = [mm(t.GetStart().x) - 100, mm(t.GetEnd().x) - 100]; ys = [mm(t.GetStart().y) - 100, mm(t.GetEnd().y) - 100]
        inside = not (max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1)
    if inside:
        R.remove(b, t); n += 1; nets.add(net)
print(f'removed {n} items of {len(nets)} nets: {", ".join(sorted(nets))}', flush=True)
pcbnew.SaveBoard(out, b)
gndfix.remove_dangling(b, out, log=print, locked=False)
pcbnew.SaveBoard(out, b)
