#!/usr/bin/env python3
"""copy the DSI fan-out at J302 (tracks / vias of the DSI nets wholly west of x 19.6) from ORIG into BOARD where it is
missing. usage: restore_fanout.py ORIG BOARD"""
import os
import sys, pcbnew
orig, path = sys.argv[1:3]
a = pcbnew.LoadBoard(orig); b = pcbnew.LoadBoard(path)
mm = pcbnew.ToMM
X = 19.6
def key(t):
    if t.GetClass() == 'PCB_VIA':
        p = t.GetPosition(); return ('v', t.GetNetname(), p.x, p.y)
    return ('t', t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y)
have = {key(t) for t in b.GetTracks()}
n = 0
for t in a.GetTracks():
    if not t.GetNetname().split('/')[-1].startswith('DSI_'):
        continue
    pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
    if not all(mm(q.x) - 100 < X for q in pts) or key(t) in have:
        continue
    c = t.Duplicate()
    c.SetNet(b.FindNet(t.GetNetname()))
    b.Add(c)
    n += 1
pcbnew.SaveBoard(path, b)
print(f'restored {n} fan-out items')
