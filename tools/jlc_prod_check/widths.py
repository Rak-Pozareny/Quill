"""Track widths: ours (KiCad Gerber, mm) against JLCPCB's production layer (jlccam, inches), matched by centreline.

usage: python3 -I widths.py JLC_LAYER OUR_GERBER [NETS.tsv]

For every straight draw of ours (a track), the JLC draw whose centreline runs through our draw's midpoint, parallel,
within TOL. Prints a table: our width -> their width, count, and the nets; unmatched draws listed by place.
"""
import collections
import math
import re
import sys

from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

DX, DY = 100.0, -172.0
TOL = 0.004


def draws(path, jlc):
    txt = open(path).read().replace('\r', '')
    toks = re.findall(r'%[^%]*%|[^%*\s][^*]*\*', txt)
    aps, div, scale, cur, x, y, mode, region, net, out = {}, 1e6, 1.0, None, 0, 0, 1, False, None, []
    for t in toks:
        if t.startswith('%'):
            b = t[1:-1].replace('\n', '')
            if b.startswith('FS'): div = 10 ** int(re.match(r'FSLAX(\d)(\d)', b).group(2))
            elif b.startswith('MO'): scale = 25.4 if b.startswith('MOIN') else 1.0
            elif b.startswith('ADD'):
                m = re.match(r'ADD(\d+)([A-Za-z_][A-Za-z_0-9]*),?([^*]*)\*', b)
                aps[int(m.group(1))] = (m.group(2), [float(v) for v in m.group(3).split('X')] if m.group(3) else [])
            elif b.startswith('TO.N,'): net = b[5:-1]
            elif b.startswith('TD'): net = None
            continue
        t = t[:-1]
        if t.startswith('G04') or not t: continue
        if t.startswith('G54'): t = t[3:]
        if t == 'G36': region = True; continue
        if t == 'G37': region = False; continue
        m = re.match(r'^G0?([123])(.*)$', t)
        if m:
            mode = int(m.group(1)); t = m.group(2)
            if not t: continue
        if re.match(r'^(G\d+|M02)$', t): continue
        m = re.match(r'^D(\d+)$', t)
        if m and int(m.group(1)) >= 10: cur = int(m.group(1)); continue
        m = re.match(r'^(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])$', t)
        if not m: continue
        nx = int(m.group(1)) / div * scale if m.group(1) is not None else x
        ny = int(m.group(2)) / div * scale if m.group(2) is not None else y
        if int(m.group(5)) == 1 and not region and mode == 1 and aps[cur][0] == 'C' and (nx, ny) != (x, y):
            a, b = (x, y), (nx, ny)
            if jlc: a, b = (a[0] + DX, a[1] + DY), (b[0] + DX, b[1] + DY)
            out.append((a, b, round(aps[cur][1][0] * scale, 4), net))
        x, y = nx, ny
    return out


ours = draws(sys.argv[2], False)
theirs = draws(sys.argv[1], True)
lines = [LineString([a, b]) for a, b, w, n in theirs]
tree = STRtree(lines)
table = collections.defaultdict(lambda: [0, set()])
unmatched = []
for a, b, w, n in ours:
    mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    ux, uy = b[0] - a[0], b[1] - a[1]; L = math.hypot(ux, uy); ux, uy = ux / L, uy / L
    best = None
    for k in tree.query(mid.buffer(TOL)):
        ta, tb, tw, _ = theirs[k]
        vx, vy = tb[0] - ta[0], tb[1] - ta[1]; M = math.hypot(vx, vy)
        if M == 0 or abs(ux * vy - uy * vx) / M > 0.02: continue
        d = lines[k].distance(mid)
        if d <= TOL and (best is None or d < best[0]): best = (d, tw)
    if best is None:
        unmatched.append((w, n, mid.x, -mid.y, L))
    else:
        e = table[(w, best[1])]; e[0] += 1; e[1].add((n or '?').split('/')[-1])
print(f'{sys.argv[1]}: our draws {len(ours)}, theirs {len(theirs)}')
for (w, tw), (c, nets) in sorted(table.items()):
    ns = sorted(nets)
    print(f'  {w:.4f} -> {tw:.4f} (+{tw - w:.4f})  {c:5d} segs  nets {len(ns)}: {", ".join(ns[:12])}{" ..." if len(ns) > 12 else ""}')
print(f'  unmatched: {len(unmatched)}')
by = collections.Counter((u[0], (u[1] or '?').split('/')[-1]) for u in unmatched)
for (w, n), c in by.most_common(40):
    ex = next(u for u in unmatched if u[0] == w and (u[1] or '?').split('/')[-1] == n)
    print(f'    {w:.4f} {n:28s} {c:4d} segs  e.g. at KiCad ({ex[2]:.3f}, {ex[3]:.3f}) len {ex[4]:.3f}')
