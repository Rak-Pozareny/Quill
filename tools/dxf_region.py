#!/usr/bin/env python3
"""List polyline 'circles'/shapes and SOLID pads of given layers inside a region.
usage: dxf_region.py FILE x0 y0 x1 y1 LAYER [LAYER...]"""
import sys, math, collections
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dxf_summary import entities
fn = sys.argv[1]; x0, y0, x1, y1 = map(float, sys.argv[2:6]); layers = set(sys.argv[6:])
cur = None; shapes = []; solids = []
for e in entities(fn):
    t = e['type']; lay = e['g'].get('8', '?')
    if t == 'POLYLINE':
        cur = {'layer': lay, 'v': []}
    elif t == 'VERTEX' and cur is not None:
        x, y = e['pts'][0]; cur['v'].append((x, y, float(e['g'].get('42', 0) or 0)))
    elif t == 'SEQEND' and cur is not None:
        if cur['layer'] in layers: shapes.append(cur)
        cur = None
    elif t == 'SOLID' and lay in layers:
        pts = [p for p in e['pts'] if p[1] is not None]
        solids.append((lay, pts))
def inside(x, y): return x0 <= x <= x1 and y0 <= y <= y1
for s in shapes:
    xs = [v[0] for v in s['v']]; ys = [v[1] for v in s['v']]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    if inside(cx, cy):
        print(f"SHAPE {s['layer']} n={len(s['v'])} c=({cx:.3f},{cy:.3f}) size {max(xs)-min(xs):.3f}x{max(ys)-min(ys):.3f} bulges={[round(v[2],2) for v in s['v']]}")
cnt = collections.Counter()
pads = []
for lay, pts in solids:
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    if inside(cx, cy):
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        pads.append((cx, cy, round(w, 3), round(h, 3)))
        cnt[(round(w, 3), round(h, 3))] += 1
print('SOLID pad sizes in region:', cnt.most_common(12))
if '--pads' in sys.argv:
    for p in pads: print('PAD', p)
