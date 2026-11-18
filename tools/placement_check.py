#!/usr/bin/env python3
"""Placement quality report for a board (pad-centre distances, before routing).

usage: placement_check.py BOARD.kicad_pcb [limit_mm]
1. Decoupling: every capacitor from a rail to GND, distance from its rail pad to the nearest pin on that rail of an
   IC, connector, transistor, inductor or current-sense resistor (2512). Listed when above the limit (default 4 mm),
   with its schematic group.
2. Switch nodes: every inductor pad on a switching net, distance to the nearest switch pin.
3. Sensitive nets (feedback, compensation, current-sense filter, gate drive, bootstrap): the minimum spanning
   tree over the pad centres of the net, as an estimate of the routed length.
"""
import json
import math
import os
import re
import sys

import pcbnew

board = sys.argv[1]
limit = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
b = pcbnew.LoadBoard(board)
gj = os.path.join(os.path.dirname(os.path.abspath(board)), 'groups.json')
groups = json.load(open(gj)) if os.path.exists(gj) else {}
fps = {f.GetReference(): f for f in b.GetFootprints()}


def xy(p):
    q = p.GetPosition()
    return pcbnew.ToMM(q.x) - 100, pcbnew.ToMM(q.y) - 100


def side(f):
    return 'B' if f.IsFlipped() else 'F'


def short(n):
    return n.split('/')[-1]


pads_by_net = {}
for r, f in fps.items():
    for p in f.Pads():
        if p.GetNetname():
            pads_by_net.setdefault(short(p.GetNetname()), []).append((r, p))


def anchor_ok(r, f):
    return bool(re.match(r'(U|J|Q|L)\d', r)) or (r.startswith('R') and '2512' in str(f.GetFPID().GetLibItemName()))


print(f'== 1. decoupling capacitors farther than {limit} mm from a pin on their rail')
bad = []
for r, f in sorted(fps.items()):
    if not r.startswith('C'):
        continue
    nets = {short(p.GetNetname()) for p in f.Pads()}
    if len(nets) != 2 or 'GND' not in nets:
        continue
    rail = (nets - {'GND'}).pop()
    cands = [(rr, p) for rr, p in pads_by_net.get(rail, []) if rr != r and anchor_ok(rr, fps[rr])]
    if not cands:
        continue
    cp = next(p for p in f.Pads() if short(p.GetNetname()) == rail)
    d, rr = min((math.dist(xy(p), xy(cp)), rr) for rr, p in cands)
    if d > limit:
        bad.append((round(d, 1), r, f.GetValue(), rail, rr, side(f), groups.get(r, '')[:60]))
for t in sorted(bad, reverse=True):
    print('  %5.1f mm  %-5s %-12s %-14s nearest %-5s (%s)  [%s]' % t)
print(f'  {len(bad)} capacitors above {limit} mm')

print('\n== 2. switch nodes: inductor pad to the nearest switch pin')
SW = re.compile(r'(_SW\d?$|_SW$|_L1$|_L2$|VLX$|^BL_SW$)')
for r, f in sorted(fps.items()):
    if not re.match(r'L\d', r):
        continue
    for p in f.Pads():
        n = short(p.GetNetname())
        if not SW.search(n):
            continue
        others = [(math.dist(xy(p), xy(q)), rr + '.' + q.GetNumber()) for rr, q in pads_by_net[n]
                  if rr != r and re.match(r'(U|Q)\d', rr)]
        if others:
            d, who = min(others)
            print('  %-5s pad %s %-16s %4.1f mm to %s' % (r, p.GetNumber(), n, d, who))

print('\n== 3. sensitive nets: spanning length over pad centres')
SENS = re.compile(r'(_FB$|_COMP|_HIDRV|_LODRV|_BTST|_BOOT$|_SRP$|_SRN$|_ACP$|_ACN$|_ILIM$|_FSW$|_VINA$|_REGN$|_VCC$)')
for n in sorted(pads_by_net):
    if not SENS.search(n):
        continue
    ps = [(rr + '.' + p.GetNumber() + side(fps[rr]), xy(p)) for rr, p in pads_by_net[n]]
    inside, tot = {0}, 0.0
    while len(inside) < len(ps):
        d, j = min((math.dist(ps[i][1], ps[k][1]), k) for i in inside for k in range(len(ps)) if k not in inside)
        inside.add(j)
        tot += d
    print('  %-22s %5.1f mm  %s' % (n, tot, ' '.join(x[0] for x in ps)))
