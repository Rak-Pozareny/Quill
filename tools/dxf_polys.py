#!/usr/bin/env python3
"""R12 DXF: assemble POLYLINE/VERTEX entities (with bulge) and report per layer; detect circles drawn as 2 bulged vertices.
usage: dxf_polys.py FILE LAYER [LAYER...]"""
import sys, math
sys.path.insert(0, __import__('os').path.dirname(__file__))
from dxf_summary import entities
fn = sys.argv[1]; layers = set(sys.argv[2:])
polys = []; cur = None
for e in entities(fn):
    t = e['type']; lay = e['g'].get('8', '?')
    if t == 'POLYLINE':
        cur = {'layer': lay, 'v': [], 'closed': int(e['g'].get('70', '0')) & 1, 'w': float(e['g'].get('40', 0) or 0)}
    elif t == 'VERTEX' and cur is not None:
        x, y = e['pts'][0]
        cur['v'].append((x, y, float(e['g'].get('42', 0) or 0)))
    elif t == 'SEQEND' and cur is not None:
        if cur['layer'] in layers: polys.append(cur)
        cur = None
for p in polys:
    v = p['v']
    xs = [q[0] for q in v]; ys = [q[1] for q in v]
    desc = f"{p['layer']} n={len(v)} closed={p['closed']} w={p['w']:.3f} bbox x[{min(xs):.3f},{max(xs):.3f}] y[{min(ys):.3f},{max(ys):.3f}]"
    if len(v) == 2 and abs(abs(v[0][2]) - 1) < 1e-3 and abs(abs(v[1][2]) - 1) < 1e-3:
        cx, cy = (v[0][0] + v[1][0]) / 2, (v[0][1] + v[1][1]) / 2
        r = math.hypot(v[0][0] - v[1][0], v[0][1] - v[1][1]) / 2
        desc = f"CIRCLE {p['layer']} c=({cx:.3f},{cy:.3f}) r={r:.3f} w={p['w']:.3f}"
    print(desc)
