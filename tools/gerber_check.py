#!/usr/bin/env python3
"""The copper of a Gerber zip checked the way a fab's CAM builds it (D116): what JLCPCB receives, not KiCad's model.

usage: gerber_check.py GERBER.zip NAME [REPORT.txt]        (needs shapely; run with python3 -I)

Every copper layer is rebuilt from its Gerber (flashes, track draws, pour regions, aperture macros) and the plated
holes from the Excellon file; KiCad's X2 attributes give each object its net and each pad its reference.

1. Shorts: copper of two nets in one island (a net tie, a footprint whose reference starts with NT, is allowed).
2. Opens: the pads of every net must form one piece through copper and plated holes. Copper that only touches at a
   point stays two pieces, so the failure of board A's first order (D110) shows here as an open.
3. Necks: each layer eroded by NECK_E; an island whose pads, vias and track middles fall apart is joined somewhere by
   copper narrower than 2 x NECK_E (0.095 mm, 95 % of the thinnest track).
4. Joints: every overlap of two same-net objects, measured through the copper around it against the narrower of the
   two (a pour counts as 0.15 mm). Under 95 %: NEEDED when a net's pads fall apart without it, "isolates" when some
   copper does, "pour" when a pour is involved, else redundant (a via overlapping the pad its track already joins).
5. Copper with a net but no pad in its piece (a pour island held by nothing).

Exit status 1 for any short, open, neck, NEEDED / isolates / pour joint or held-by-nothing copper; redundant joints
are listed only.
"""
import collections
import math
import os
import re
import sys

import shapely
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import nearest_points, polylabel, unary_union
from shapely.strtree import STRtree

LAYERS = ['F_Cu', 'In1_Cu', 'In2_Cu', 'In3_Cu', 'In4_Cu', 'B_Cu']
RES = 32                     # segments per quarter circle
ARITH = re.compile(r'^[0-9.+\-*/() ]+$')


def ev(expr, args):
    s = re.sub(r'\$(\d+)', lambda m: '(%.9f)' % args[int(m.group(1)) - 1], expr).replace('x', '*').replace('X', '*')
    if not ARITH.match(s):
        raise ValueError('macro expression ' + expr)
    return float(eval(s, {'__builtins__': {}}, {}))


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    return [p for p in getattr(g, 'geoms', []) if isinstance(p, (Polygon, MultiPolygon)) for p in polys(p)]


def macro_shape(body, args):
    dark, clear = [], []
    for st in body:
        f = [x.strip() for x in st.split(',')]
        code = int(f[0])
        if code == 0:
            continue
        v = [ev(x, args) for x in f[1:]]
        exp = v[0]
        if code == 1:
            d, cx, cy = v[1], v[2], v[3]
            rot = v[4] if len(v) > 4 else 0
            g = Point(cx, cy).buffer(d / 2, RES)
        elif code == 4:
            n = int(v[1])
            pts = [(v[2 + 2 * i], v[3 + 2 * i]) for i in range(n + 1)]
            rot = v[2 + 2 * (n + 1)]
            g = shapely.make_valid(Polygon(pts))
        elif code == 20:
            w, x1, y1, x2, y2, rot = v[1:7]
            g = LineString([(x1, y1), (x2, y2)]).buffer(w / 2, cap_style='flat')
        elif code == 21:
            w, h, cx, cy, rot = v[1:6]
            g = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        else:
            raise ValueError('macro primitive %d' % code)
        if rot:
            g = affinity.rotate(g, rot, origin=(0, 0))
        (dark if exp == 1 else clear).append(g)
    g = unary_union(dark)
    if clear:
        g = g.difference(unary_union(clear))
    return g


def aperture_shape(ap, macros):
    kind, p = ap
    if kind == 'C':
        return Point(0, 0).buffer(p[0] / 2, RES)
    if kind == 'R':
        return box(-p[0] / 2, -p[1] / 2, p[0] / 2, p[1] / 2)
    if kind == 'O':
        w, h = p[0], p[1]
        if w >= h:
            return LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, RES)
        return LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, RES)
    if kind in macros:
        return macro_shape(macros[kind], p)
    raise ValueError('aperture ' + kind)


def parse_gerber(path):
    txt = open(path).read()
    toks, i = [], 0
    while i < len(txt):
        c = txt[i]
        if c == '%':
            j = txt.index('%', i + 1)
            toks.append(('X', txt[i + 1:j].replace('\n', '').replace('\r', '')))
            i = j + 1
        elif c in ' \r\n':
            i += 1
        else:
            j = txt.index('*', i)
            toks.append(('C', txt[i:j]))
            i = j + 1
    macros, aps, apattr, ta, to = {}, {}, {}, {}, {}
    div = 1e6
    cur, x, y = None, 0.0, 0.0
    region, contour, contours = False, [], []
    objs = []
    shape_cache = {}

    def emit(kind, geom, anchor, width=None, p0=None, p1=None):
        objs.append(dict(kind=kind, geom=geom, anchor=anchor, width=width, p0=p0, p1=p1, ap=cur, net=to.get('N'), pad=to.get('P'),
                         func=apattr.get(cur, {}).get('AperFunction') if kind != 'region' else ta.get('AperFunction')))

    for typ, t in toks:
        if typ == 'X':
            if t.startswith('FS'):
                m = re.match(r'FSLAX(\d)(\d)Y(\d)(\d)', t)
                div = 10 ** int(m.group(2))
            elif t.startswith('MO'):
                assert t.startswith('MOMM'), t
            elif t.startswith('AM'):
                parts = [s for s in t[2:].split('*') if s]
                name, body = parts[0], [s for s in parts[1:] if not s.startswith('0 ')]
                macros[name] = body
            elif t.startswith('AD'):
                m = re.match(r'ADD(\d+)([A-Za-z_][A-Za-z_0-9]*),?([^*]*)\*', t)
                code, kind, params = int(m.group(1)), m.group(2), m.group(3)
                aps[code] = (kind, [float(v) for v in params.split('X')] if params else [])
                apattr[code] = dict(ta)
            elif t.startswith('TA'):
                k, _, v = t[3:-1].partition(',')
                ta[k] = v
            elif t.startswith('TO'):
                k, _, v = t[3:-1].partition(',')
                to[k] = v
            elif t.startswith('TD'):
                k = t[2:-1].lstrip('.')
                if k:
                    ta.pop(k, None)
                    to.pop(k, None)
                else:
                    ta.clear()
                    to.clear()
            elif t.startswith('LP'):
                assert t.startswith('LPD'), 'clear polarity not handled: ' + t
            continue
        if t.startswith('G04') or t in ('G01', 'G75', 'M02') or not t:
            continue
        if t == 'G36':
            region, contours, contour = True, [], []
            continue
        if t == 'G37':
            if len(contour) > 2:
                contours.append(contour)
            for cpts in contours:
                g = shapely.make_valid(Polygon(cpts))
                for pg in polys(g):
                    emit('region', pg, None)
            region, contours, contour = False, [], []
            continue
        if t.startswith('G02') or t.startswith('G03'):
            raise ValueError('arc in ' + path)
        if t.startswith('G01'):
            t = t[3:]
        m = re.match(r'^D(\d+)$', t)
        if m and int(m.group(1)) >= 10:
            cur = int(m.group(1))
            continue
        m = re.match(r'^(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])$', t)
        if not m:
            raise ValueError('unhandled %r in %s' % (t, path))
        nx = int(m.group(1)) / div if m.group(1) is not None else x
        ny = int(m.group(2)) / div if m.group(2) is not None else y
        d = int(m.group(5))
        if region:
            if d == 2:
                if len(contour) > 2:
                    contours.append(contour)
                contour = [(nx, ny)]
            elif d == 1:
                contour.append((nx, ny))
        elif d == 1:
            kind, p = aps[cur]
            assert kind == 'C', 'draw with non-circular aperture'
            if (nx, ny) == (x, y):
                g = Point(x, y).buffer(p[0] / 2, RES)
            else:
                g = LineString([(x, y), (nx, ny)]).buffer(p[0] / 2, RES)
            emit('draw', g, ((x + nx) / 2, (y + ny) / 2), width=p[0], p0=(x, y), p1=(nx, ny))
        elif d == 3:
            if cur not in shape_cache:
                shape_cache[cur] = aperture_shape(aps[cur], macros)
            g = affinity.translate(shape_cache[cur], nx, ny)
            emit('flash', g, (nx, ny))
        x, y = nx, ny
    return objs


def parse_drill(path):
    tools, attr, cur, holes = {}, None, None, []
    for line in open(path):
        line = line.strip()
        if line.startswith('; #@! TA.AperFunction'):
            attr = line.split(',', 1)[1]
            continue
        m = re.match(r'^T(\d+)C([\d.]+)$', line)
        if m:
            tools[int(m.group(1))] = (float(m.group(2)), attr)
            continue
        m = re.match(r'^T(\d+)$', line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r'^X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?$', line)
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            end = (float(m.group(3)), float(m.group(4))) if m.group(3) else None
            holes.append(dict(x=x, y=y, end=end, d=tools[cur][0], func=tools[cur][1]))
        elif line.startswith(('G00', 'M15', 'M16', 'G01')):
            raise ValueError('routed slot not handled: ' + line)
    return holes


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def netname(n):
    return n if n else ''



GOOD = 0.95
REGION_HW = 0.075
TOL = 1e-4


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def halfwidth(o, cache):
    if o['kind'] == 'draw':
        return o['width'] / 2
    if o['kind'] == 'region':
        return REGION_HW
    k = o['ap']
    if k not in cache:
        g = o['geom']
        g = max(polys(g), key=lambda q: q.area)
        c = polylabel(g, 0.0005)
        cache[k] = g.exterior.distance(c)
    return cache[k]


def trivially_full(a, b):
    """True when the joint is plainly full width: an end on the other's centre line, a via on a track's centre line,
    a flash inside a flash or region, a track end deep in a pad"""
    for x, y in ((a, b), (b, a)):
        if x['kind'] == 'draw' and y['kind'] == 'draw':
            for E in (x['p0'], x['p1']):
                if seg_dist(E, y['p0'], y['p1']) < TOL:
                    return True
        if x['kind'] == 'draw' and y['kind'] == 'flash':
            if seg_dist(y['anchor'], x['p0'], x['p1']) < TOL:
                return True
            for E in (x['p0'], x['p1']):
                if Point(E).buffer(x['width'] / 2, 16).within(y['geom']):
                    return True
        if x['kind'] == 'flash' and y['kind'] in ('flash', 'region') and x['geom'].within(y['geom']):
            return True
        if x['kind'] == 'draw' and y['kind'] == 'region':
            for E in (x['p0'], x['p1']):
                if Point(E).buffer(x['width'] / 2, 16).within(y['geom']):
                    return True
    return False


def joint(a, b, ha, hb, local=None):
    """(J, ratio, location); local: all same-net geometry near the joint, to measure through the copper around it"""
    I = a['geom'].intersection(b['geom'])
    if I.is_empty:
        return 0.0, 0.0, None
    c = I.centroid
    emax = min(ha, hb)
    x0, y0, x1, y1 = I.bounds
    m = 1.0
    A = shapely.clip_by_rect(a['geom'], x0 - m, y0 - m, x1 + m, y1 + m)
    B = shapely.clip_by_rect(b['geom'], x0 - m, y0 - m, x1 + m, y1 + m)
    parts = [A, B] + [shapely.clip_by_rect(g, x0 - m, y0 - m, x1 + m, y1 + m) for g in (local or [])]
    U = unary_union(parts)
    da = A.buffer(-0.995 * emax, 16)
    db = B.buffer(-0.995 * emax, 16)
    if da.is_empty or db.is_empty:
        return None, None, c
    pa = nearest_points(da, c)[0]
    pb = nearest_points(db, c)[0]

    def together(e):
        E = U.buffer(-e, 16)
        for q in polys(E):
            ia, ib = q.distance(pa) < 1e-7, q.distance(pb) < 1e-7
            if ia or ib:
                return ia and ib
        return False

    lo, hi = 0.0, 0.99 * emax
    if together(hi):
        return 2 * emax, 1.0, c
    if not together(1e-6):
        return 0.0, 0.0, c
    for _ in range(14):
        mid = (lo + hi) / 2
        if together(mid):
            lo = mid
        else:
            hi = mid
    return 2 * lo, lo / emax, c


def short(n):
    return (n or '').split('/')[-1]




NECK_E = 0.0475


def kind(o):
    if o['kind'] == 'draw':
        return f'track {o["width"]:.3f}'
    if o['kind'] == 'flash':
        return 'via' if (o['func'] or '').startswith('Via') else 'pad ' + (o['pad'] or '?')
    return 'pour'


def main():
    import tempfile
    import zipfile
    zpath, name = sys.argv[1], sys.argv[2]
    report = sys.argv[3] if len(sys.argv) > 3 else None
    out = []

    def say(s=''):
        print(s)
        out.append(s)
    with tempfile.TemporaryDirectory() as gdir:
        with zipfile.ZipFile(zpath) as z:
            for m in z.namelist():
                if '/' not in m and not m.startswith('.'):
                    with open(os.path.join(gdir, m), 'wb') as f:
                        f.write(z.read(m))
        files = {L: os.path.join(gdir, f) for f in os.listdir(gdir) for L in LAYERS if f.startswith(name + '-' + L + '.')}
        layers = {}
        for L in LAYERS:
            objs = parse_gerber(files[L])
            U = unary_union([o['geom'] for o in objs])
            comps = polys(U)
            ctree = STRtree(comps)
            for o in objs:
                pt = Point(o['anchor']) if o['anchor'] else o['geom'].representative_point()
                h = ctree.query(pt, predicate='intersects')
                if len(h) != 1:
                    h = ctree.query(o['geom'], predicate='intersects')
                o['comp'] = int(h[0]) if len(h) else None
            layers[L] = dict(objs=objs, U=U, comps=comps, ctree=ctree, otree=STRtree([o['geom'] for o in objs]))
        holes = parse_drill(os.path.join(gdir, name + '-PTH.drl'))
    say(f'{zpath}: ' + ', '.join(f'{L} {len(d["objs"])} objects / {len(d["comps"])} islands' for L, d in layers.items())
        + f'; {len(holes)} plated holes')
    fail = 0

    # 1. shorts
    shorts = []
    for L, d in layers.items():
        nets, refs = collections.defaultdict(set), collections.defaultdict(set)
        for o in d['objs']:
            if o['net'] and o['comp'] is not None:
                nets[o['comp']].add(o['net'])
                if o['pad']:
                    refs[o['comp']].add(o['pad'].split(',')[0])
        for k, s in nets.items():
            if len(s) > 1:
                tie = any(r.startswith('NT') for r in refs[k])
                c = d['comps'][k].representative_point()
                shorts.append((L, c, s, tie))
    bad = [x for x in shorts if not x[3]]
    say(f'1. islands with two nets: {len(shorts)} ({len(shorts) - len(bad)} at a net tie); shorts: {len(bad)}')
    for L, c, s, tie in shorts:
        say(f'   {"net tie" if tie else "SHORT"} {L} ({c.x:.3f}, {-c.y:.3f}) {sorted(short(n) for n in s)}')
    fail += len(bad)

    # 2. opens
    uf = UF()
    for L, d in layers.items():
        for k in range(len(d['comps'])):
            uf.find((L, k))
    for h in holes:
        pt = Point(((h['x'] + h['end'][0]) / 2, (h['y'] + h['end'][1]) / 2)) if h['end'] else Point(h['x'], h['y'])
        nodes = [(L, int(k)) for L, d in layers.items() for k in d['ctree'].query(pt, predicate='intersects')]
        for n in nodes[1:]:
            uf.union(nodes[0], n)
    netg = collections.defaultdict(lambda: collections.defaultdict(list))
    haspad = set()
    for L, d in layers.items():
        for o in d['objs']:
            if o['pad'] and o['comp'] is not None:
                g = uf.find((L, o['comp']))
                haspad.add(g)
                if o['net'] and o['net'] != 'N/C' and not o['net'].startswith('unconnected-'):
                    netg[o['net']][g].append(o['pad'])
    opens = {n: g for n, g in netg.items() if len(g) > 1}
    say(f'2. nets with pads: {len(netg)}; opens: {len(opens)}')
    for n, g in opens.items():
        say(f'   OPEN {short(n)}: ' + ' | '.join(','.join(sorted(set(v)))[:100] for v in g.values()))
    fail += len(opens)

    # 3. necks
    splits = []
    for L, d in layers.items():
        pieces = polys(d['U'].buffer(-NECK_E, RES))
        pt = STRtree(pieces)
        per = collections.defaultdict(lambda: collections.defaultdict(list))
        for o in d['objs']:
            if o['comp'] is None or o['kind'] == 'region' or (o['kind'] == 'draw' and o['width'] <= 2 * NECK_E + 0.001):
                continue
            h = pt.query(Point(o['anchor']), predicate='intersects')
            if len(h):
                per[o['comp']][int(h[0])].append(o)
        for k, byp in per.items():
            if len(byp) > 1:
                o = list(byp.values())[0][0]
                splits.append(f'   NECK {L} near ({o["anchor"][0]:.3f}, {-o["anchor"][1]:.3f}) {short(o["net"])}: '
                              f'{len(byp)} parts')
    say(f'3. copper narrower than {2 * NECK_E:.3f} mm joining two parts of an island: {len(splits)}')
    for s in splits:
        say(s)
    fail += len(splits)

    # 4. joints
    cache, weak, good = {}, [], []
    for L, d in layers.items():
        objs, tree = d['objs'], d['otree']
        cache.clear()
        hw = [halfwidth(o, cache) for o in objs]
        geoms = [o['geom'] for o in objs]
        ii, jj = tree.query(geoms, predicate='intersects')
        for i, j in zip(ii, jj):
            if i >= j:
                continue
            a, b = objs[i], objs[j]
            if not a['net'] or a['net'] != b['net']:
                continue
            if trivially_full(a, b):
                good.append(((L, i), (L, j)))
                continue
            J, r, c = joint(a, b, hw[i], hw[j])
            if J is not None and r < GOOD and c is not None:
                near = [objs[k]['geom'] for k in tree.query(c.buffer(1.0), predicate='intersects')
                        if k not in (i, j) and objs[k]['net'] == a['net']]
                if near:
                    J2, r2, _ = joint(a, b, hw[i], hw[j], near)
                    if J2 is not None and r2 > r:
                        J, r = J2, r2
            if J is None or r >= GOOD:
                good.append(((L, i), (L, j)))
            else:
                weak.append(dict(L=L, i=i, j=j, a=a, b=b, J=J, r=r, c=c, ref=2 * min(hw[i], hw[j])))
    ug = UF()
    for x, y in good:
        ug.union(x, y)
    for h in holes:
        pt = Point(((h['x'] + h['end'][0]) / 2, (h['y'] + h['end'][1]) / 2)) if h['end'] else Point(h['x'], h['y'])
        nodes = [(L, int(k)) for L, d in layers.items() for k in d['otree'].query(pt, predicate='intersects')
                 if d['objs'][k]['kind'] != 'draw']
        for n in nodes[1:]:
            ug.union(nodes[0], n)
    pads = collections.defaultdict(lambda: collections.defaultdict(list))
    for L, d in layers.items():
        for k, o in enumerate(d['objs']):
            ug.find((L, k))
            if o['pad'] and o['net'] and o['net'] != 'N/C' and not o['net'].startswith('unconnected-'):
                pads[o['net']][ug.find((L, k))].append(o['pad'])
    split = {n: g for n, g in pads.items() if len(g) > 1}
    tags = collections.Counter()
    for w in weak:
        ga, gb = ug.find((w['L'], w['i'])), ug.find((w['L'], w['j']))
        n = w['a']['net']
        if ga != gb and n in split and ga in split[n] and gb in split[n]:
            w['tag'] = 'NEEDED'
        elif ga != gb:
            w['tag'] = 'isolates'
        elif 'region' in (w['a']['kind'], w['b']['kind']):
            w['tag'] = 'pour'
        else:
            w['tag'] = 'redundant'
        tags[w['tag']] += 1
    say(f'4. same-net joints under {GOOD:.0%} of the narrower object: {len(weak)} '
        f'(NEEDED {tags["NEEDED"]}, isolates {tags["isolates"]}, pour {tags["pour"]}, redundant {tags["redundant"]})')
    order = {'NEEDED': 0, 'isolates': 1, 'pour': 2, 'redundant': 3}
    for w in sorted(weak, key=lambda w: (order[w['tag']], w['r'])):
        c = w['c']
        say(f'   {w["tag"]:9s} {w["L"]:6s} ({c.x:.3f}, {-c.y:.3f}) {short(w["a"]["net"]):18s} {kind(w["a"])} + '
            f'{kind(w["b"])}: {w["J"]:.4f} of {w["ref"]:.3f} mm ({w["r"]:.0%})')
    fail += tags['NEEDED'] + tags['isolates'] + tags['pour']

    # 5. copper held by nothing
    held = 0
    members = collections.defaultdict(list)
    for L, d in layers.items():
        for k in range(len(d['comps'])):
            members[uf.find((L, k))].append((L, k))
    for g, mem in members.items():
        if g in haspad:
            continue
        nets = {o['net'] for L, k in mem for o in layers[L]['objs'] if o['comp'] == k and o['net']}
        if nets:
            held += 1
            L, k = mem[0]
            c = layers[L]['comps'][k].representative_point()
            say(f'   NO PAD {L} ({c.x:.3f}, {-c.y:.3f}) {sorted(short(n) for n in nets)}')
    say(f'5. copper with a net but no pad in its piece: {held}')
    fail += held
    say(f'result: {"FAIL" if fail else "pass"} ({fail} findings)')
    if report:
        with open(report, 'w') as f:
            f.write('\n'.join(out) + '\n')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
