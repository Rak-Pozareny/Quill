"""Copper JLCPCB added (theirs, beyond compensation) and which of our nets each piece touches.

usage: python3 -I added_nets.py TOOLS_DIR JLC_LAYER OUR_GERBER OUR_EDGE_CUTS
A piece touching two nets would be a short; touching none, floating copper.
"""
import collections
import sys

sys.path.insert(0, sys.argv[1])
import gerber_check as gc                                     # our own tool, reads our own Gerbers
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import jlc_vs_ours as jv
from shapely import affinity
from shapely.ops import polygonize, unary_union
from shapely.strtree import STRtree

jlc, ours, edge = sys.argv[2:5]
T = affinity.translate(jv.parse(jlc), jv.DX, jv.DY)
objs = gc.parse_gerber(ours)
O = unary_union([o['geom'] for o in objs])
board = max(polygonize(unary_union(jv.parse(edge)).boundary), key=lambda p: p.area).buffer(-0.03)
extra = T.intersection(board).buffer(-0.03).difference(O)
pieces = [p for p in getattr(extra, 'geoms', [extra]) if p.area > 0.0003]
geoms = [o['geom'] for o in objs]
tree = STRtree(geoms)
counts = collections.Counter()
flag = []
for p in pieces:
    near = tree.query(p.buffer(0.06))
    nets = {gc.netname(objs[k]['net']) if objs[k]['net'] else '(no net)' for k in near if geoms[k].distance(p) < 0.06}
    counts[len(nets)] += 1
    if len(nets) != 1:
        c = p.centroid
        flag.append((p.area, c.x, -c.y, sorted(nets)))
print(f'{jlc}: {len(pieces)} added pieces; by number of nets touched: {dict(sorted(counts.items()))}')
for a, x, y, n in sorted(flag, reverse=True)[:30]:
    print(f'   area {a:.4f} at KiCad ({x:.3f}, {y:.3f}): {n}')
