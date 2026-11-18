"""Compare JLCPCB's production copper (jlccam Gerber, inches, arcs, LPD/LPC) with our KiCad Gerbers, inside the board.

usage: python3 -I jlc_vs_ours.py JLC_LAYER OUR_GERBER OUR_EDGE_CUTS OUT_PREFIX [TOOLS_DIR]

JLC panel coordinates (inches) map to our Gerber coordinates (mm): x = 25.4 X + DX, y = 25.4 Y + DY, DX / DY from
the outlines (set below). Prints the XOR area and every difference piece over a size floor, with position in KiCad
coordinates (y down) and whether it is extra (theirs only) or missing (ours only).
"""
import math
import re
import sys

import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

RES = 8
DX, DY = 100.0, -172.0


def arc_pts(x0, y0, x1, y1, cx, cy, cw):
    a0, a1 = math.atan2(y0 - cy, x0 - cx), math.atan2(y1 - cy, x1 - cx)
    r = math.hypot(x0 - cx, y0 - cy)
    if cw:
        while a1 >= a0: a1 -= 2 * math.pi
    else:
        while a1 <= a0: a1 += 2 * math.pi
    if abs(a1 - a0) < 1e-9 or (abs(x0 - x1) < 1e-9 and abs(y0 - y1) < 1e-9):
        a1 = a0 + (-2 * math.pi if cw else 2 * math.pi)
    n = max(4, int(abs(a1 - a0) / (math.pi / 32)) + 1)
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), cy + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(1, n + 1)]


def ev(expr, args):
    s = re.sub(r'\$(\d+)', lambda m: '(%.9f)' % args[int(m.group(1)) - 1], expr).replace('x', '*').replace('X', '*')
    if not re.match(r'^[0-9.+\-*/() ]+$', s): raise ValueError(expr)
    return float(eval(s, {'__builtins__': {}}, {}))


def macro_shape(body, args):
    dark, clear = [], []
    for st in body:
        f = [x.strip() for x in st.split(',')]
        code = int(f[0])
        if code == 0: continue
        v = [ev(x, args) for x in f[1:]]
        if code == 1:
            g = Point(v[2], v[3]).buffer(v[1] / 2, RES); rot = v[4] if len(v) > 4 else 0
        elif code == 4:
            n = int(v[1]); g = shapely.make_valid(Polygon([(v[2 + 2 * i], v[3 + 2 * i]) for i in range(n + 1)])); rot = v[2 + 2 * (n + 1)]
        elif code == 20:
            g = LineString([(v[2], v[3]), (v[4], v[5])]).buffer(v[1] / 2, cap_style='flat'); rot = v[6]
        elif code == 21:
            g = box(v[3] - v[1] / 2, v[4] - v[2] / 2, v[3] + v[1] / 2, v[4] + v[2] / 2); rot = v[5]
        else: raise ValueError('primitive %d' % code)
        if rot: g = affinity.rotate(g, rot, origin=(0, 0))
        (dark if v[0] == 1 else clear).append(g)
    g = unary_union(dark)
    return g.difference(unary_union(clear)) if clear else g


def ap_shape(ap, macros):
    kind, p = ap
    if kind == 'C': return Point(0, 0).buffer(p[0] / 2, RES)
    if kind == 'R': return box(-p[0] / 2, -p[1] / 2, p[0] / 2, p[1] / 2)
    if kind == 'O':
        w, h = p[0], p[1]
        if w >= h: return LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, RES)
        return LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, RES)
    if kind == 'P':
        d, n = p[0], int(p[1]); rot = p[2] if len(p) > 2 else 0
        return Polygon([(d / 2 * math.cos(math.radians(rot + 360 * k / n)), d / 2 * math.sin(math.radians(rot + 360 * k / n))) for k in range(n)])
    return macro_shape(macros[kind], p)


def parse(path, depth_only=None):
    """Copper as one geometry in mm (file units scaled), polarity applied in order. depth_only: keep only that DEPTH."""
    txt = open(path).read().replace('\r', '')
    toks, i = [], 0
    while i < len(txt):
        c = txt[i]
        if c == '%':
            j = txt.index('%', i + 1); toks.append(('X', txt[i + 1:j].replace('\n', ''))); i = j + 1
        elif c in ' \n': i += 1
        else:
            j = txt.index('*', i); toks.append(('C', txt[i:j])); i = j + 1
    macros, aps = {}, {}
    div, scale = 1e6, 1.0
    cur, x, y, mode, depth = None, 0.0, 0.0, 1, None
    region, contour, contours = False, [], []
    layers, pol, batch = [], 'D', []          # [(polarity, geometry)]

    def flush():
        nonlocal batch
        if batch: layers.append((pol, unary_union(batch))); batch = []

    def add(g):
        if depth_only is None or depth == depth_only: batch.append(g)

    for typ, t in toks:
        if typ == 'X':
            if t.startswith('FS'):
                m = re.match(r'FSLAX(\d)(\d)Y(\d)(\d)', t); div = 10 ** int(m.group(2))
            elif t.startswith('MO'): scale = 25.4 if t.startswith('MOIN') else 1.0
            elif t.startswith('AM'):
                parts = [s for s in t[2:].split('*') if s]
                macros[parts[0]] = [s for s in parts[1:] if not s.startswith('0 ')]
            elif t.startswith('AD'):
                m = re.match(r'ADD(\d+)([A-Za-z_][A-Za-z_0-9]*),?([^*]*)\*', t)
                aps[int(m.group(1))] = (m.group(2), [float(v) for v in m.group(3).split('X')] if m.group(3) else [])
            elif t.startswith('LP'):
                flush(); pol = t[2]
            continue
        if t.startswith('G04'):
            m = re.match(r'G04 -- DEPTH (\d)|G04 DEPTH (\d)', t)
            if m: depth = int(m.group(1) or m.group(2))
            continue
        if t.startswith('G54'): t = t[3:]
        if t in ('G75', 'M02', 'G74', 'G90', 'G70', 'G71') or not t: continue
        if t == 'G36': region, contours, contour = True, [], []; continue
        if t == 'G37':
            if len(contour) > 2: contours.append(contour)
            for cp in contours: add(shapely.make_valid(Polygon(cp)))
            region, contours, contour = False, [], []; continue
        m = re.match(r'^G0?([123])(.*)$', t)
        if m:
            mode = int(m.group(1)); t = m.group(2)
            if not t: continue
        m = re.match(r'^D(\d+)$', t)
        if m and int(m.group(1)) >= 10: cur = int(m.group(1)); continue
        m = re.match(r'^(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])$', t)
        if not m: raise ValueError('unhandled %r' % t)
        nx = int(m.group(1)) / div * scale if m.group(1) is not None else x
        ny = int(m.group(2)) / div * scale if m.group(2) is not None else y
        ii = int(m.group(3)) / div * scale if m.group(3) else 0.0
        jj = int(m.group(4)) / div * scale if m.group(4) else 0.0
        d = int(m.group(5))
        if d == 1 and mode in (2, 3):
            pts = arc_pts(x, y, nx, ny, x + ii, y + jj, mode == 2)
        else:
            pts = [(nx, ny)]
        if region:
            if d == 2:
                if len(contour) > 2: contours.append(contour)
                contour = [(nx, ny)]
            elif d == 1: contour += pts
        elif d == 1:
            kind, p = aps[cur]
            w = p[0] * scale
            path = [(x, y)] + pts
            if kind != 'C':
                g = unary_union([affinity.translate(affinity.scale(ap_shape(aps[cur], macros), scale, scale, origin=(0, 0)), px, py) for px, py in path])
                add(g.convex_hull)
            elif len(set(path)) == 1: add(Point(x, y).buffer(w / 2, RES))
            else: add(LineString(path).buffer(w / 2, RES))
        elif d == 3:
            g = affinity.scale(ap_shape(aps[cur], macros), scale, scale, origin=(0, 0))
            add(affinity.translate(g, nx, ny))
        x, y = nx, ny
    flush()
    out = Polygon()
    for p, g in layers:
        out = out.union(g) if p == 'D' else out.difference(g)
    return out


def edge_poly(path):
    g = parse(path)          # outline drawn as thin lines: polygonize its centreline
    from shapely.ops import polygonize
    lines = shapely.get_exterior_ring(g) if False else None
    return g


if __name__ == '__main__':
    jlc, ours, edge, outp = sys.argv[1:5]
    T = affinity.translate(parse(jlc), DX, DY)
    O = parse(ours)
    E = parse(edge)                                   # 0.05 mm outline strokes
    from shapely.ops import polygonize
    board = max(polygonize(unary_union(E).boundary), key=lambda p: p.area)
    board = board.buffer(-0.03)                       # inside the outline stroke
    T_in = T.intersection(board); O_in = O.intersection(board)
    miss = O_in.buffer(-0.02).difference(T_in)        # our copper absent from theirs (beyond 0.02 mm)
    extra = T_in.buffer(-0.03).difference(O_in)       # their copper absent from ours (beyond compensation)
    print(f'{jlc}: ours {O_in.area:.2f} mm2, theirs {T_in.area:.2f} mm2; ours-only {miss.area:.4f}, theirs-only {extra.area:.4f}')
    import collections
    for name, g in (('THEIRS ONLY', extra), ('OURS ONLY', miss)):
        pieces = [p for p in getattr(g, 'geoms', [g]) if not p.is_empty and p.area > 0.0005]
        kinds = collections.Counter(); other = []
        for p in pieces:
            b = p.bounds; w, h = b[2] - b[0], b[3] - b[1]
            if abs(w - h) < 0.02 and p.area > 0.7 * math.pi * (w / 2) ** 2:
                kinds[f'round {w + 0.04:.2f}'] += 1
            else: other.append(p)
        print(f'  {name}: {len(pieces)} pieces; round: {dict(kinds)}')
        other.sort(key=lambda p: -p.area)
        for p in other[:25]:
            c = p.centroid; b = p.bounds
            print(f'    area {p.area:8.4f} mm2  at KiCad ({c.x:8.3f}, {-c.y:8.3f})  size {b[2]-b[0]:.3f} x {b[3]-b[1]:.3f}')
    open(outp + '.wkt', 'w').write(shapely.to_wkt(unary_union([extra, miss]), rounding_precision=4))
