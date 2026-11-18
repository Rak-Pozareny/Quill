"""Length tuning of the differential pairs (after routing).

Intra-pair skew: the shorter trace of a pair gets small trapezoid bumps (45 degree flanks) pushed away from its
partner on straight coupled segments, until P and N match within 0.025 mm. A bump of height h adds 0.83 h of length;
h is capped at 2.5 x the pair gap so the pair stays coupled, the bump is clearance-checked against everything else.

Lengths are copper track lengths plus the via barrel between the layers each via joins (stack-up z of the copper
layers), the same way tools/length_report.py counts them.
"""
import heapq
import math

import pcbnew

import proute as R
from route_rules import GEOM

Z = {pcbnew.F_Cu: 0.0175, pcbnew.In1_Cu: 0.1395, pcbnew.In2_Cu: 0.2547, pcbnew.In3_Cu: 0.9087,
     pcbnew.In4_Cu: 1.0239, pcbnew.B_Cu: 1.1625}
LNAME = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.In3_Cu: 'In3', pcbnew.B_Cu: 'B'}


def net_items(board, code):
    ts, vs = [], []
    for t in R.tracks(board):
        if t.GetNetCode() != code:
            continue
        (vs if isinstance(t, pcbnew.PCB_VIA) else ts).append(t)
    return ts, vs


def _inside(t, hit, step=0.005):
    """mm of track t for which hit(point) holds (sampled every 5 um), and the crossing points of its ends: [(point
    outside -> inside boundary)] for an end inside and the other outside (bisection)"""
    a, b, ln = t.GetStart(), t.GetEnd(), pcbnew.ToMM(t.GetLength())
    at = lambda f: pcbnew.VECTOR2I(int(a.x + (b.x - a.x) * f), int(a.y + (b.y - a.y) * f))
    n = max(1, int(ln / step))
    inside = ln * sum(hit(at((k + 0.5) / n)) for k in range(n)) / n
    cross = []
    for f_in, f_out in ((0.0, 1.0), (1.0, 0.0)):
        if hit(at(f_in)) and not hit(at(f_out)):
            for _ in range(30):
                m = (f_in + f_out) / 2
                f_in, f_out = (m, f_out) if hit(at(m)) else (f_in, m)
            cross.append(at(f_out))
    return inside, cross


_STACK = {}


def _stack(board):
    """[(name, thickness mm)] of the board's copper and dielectric layers, top down, from its file's stackup"""
    fn = board.GetFileName()
    if fn not in _STACK:
        import re
        txt = open(fn).read()
        blk = txt[txt.index('(stackup'):]
        _STACK[fn] = [(m.group(1), float(m.group(3))) for m in
                      re.finditer(r'\(layer "([^"]+)"\s*\(type "([^"]+)"\)\s*\(thickness ([\d.]+)\)', blk)
                      if m.group(1).endswith('.Cu') or m.group(1).startswith('dielectric')]
    return _STACK[fn]


def layer_distance(board, a, b):
    """KiCad's BOARD_STACKUP::GetLayerDistance (mm), the via height its length calculation uses: from the first copper
    layer through the second, an outer copper layer counted whole, an inner one at either end half"""
    names = [n for n, _ in _stack(board)]
    ia, ib = sorted((names.index(board.GetLayerName(a)), names.index(board.GetLayerName(b))))
    if ia == ib:
        return 0.0
    total = 0.0
    for k in range(ia, ib + 1):
        n, th = _stack(board)[k]
        total += th / 2 if (k in (ia, ib) and n not in ('F.Cu', 'B.Cu')) else th
    return total


def length(board, code):
    """routed length as KiCad 10 counts it (LENGTH_DELAY_CALCULATION, with heights): the tracks; where a track ends on
    a via, the copper inside the via counted as the via's radius from its centre; where a chain of tracks starts at a
    pad's centre, its copper inside the pad counted as the straight line from the centre to where it leaves; each via
    as the stackup height between the outermost layers of the tracks ending on it"""
    ts, vs = net_items(board, code)
    L = sum(pcbnew.ToMM(t.GetLength()) for t in ts)
    for v in vs:
        c, r = v.GetPosition(), v.GetWidth(pcbnew.F_Cu) / 2
        hit = lambda q: (q - c).EuclideanNorm() <= r
        on = [t for t in ts if hit(t.GetStart()) or hit(t.GetEnd())]
        for t in on:
            inside, cross = _inside(t, hit)
            L += pcbnew.ToMM(r) * len(cross) - inside
        layers = {t.GetLayer() for t in on}
        # a via inside an SMD pad of its net carries the signal down to the pad's layer too (KiCad counts it)
        for fp in R.footprints(board):
            for p in R.pads(fp):
                if p.GetNetCode() == code and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.HitTest(c):
                    layers |= {l for l in (pcbnew.F_Cu, pcbnew.B_Cu) if p.IsOnLayer(l)}
        Ls = sorted(layers, key=lambda l: [n for n, _ in _stack(board)].index(board.GetLayerName(l)))
        if len(Ls) >= 2:
            L += layer_distance(board, Ls[0], Ls[-1])
    for fp in R.footprints(board):
        for p in R.pads(fp):
            if p.GetNetCode() != code:
                continue
            c = p.GetPosition()
            for t0 in [t for t in ts if p.IsOnLayer(t.GetLayer()) and (t.GetStart() == c or t.GetEnd() == c)]:
                # the chain from the centre: on through joints where exactly two ends of the layer meet
                chain, t, end = [], t0, (t0.GetEnd() if t0.GetStart() == c else t0.GetStart())
                while t is not None and t not in chain:
                    chain.append(t)
                    if not p.HitTest(end):
                        break
                    nxt = [u for u in ts if u is not t and u.GetLayer() == t.GetLayer() and end in (u.GetStart(), u.GetEnd())]
                    t = nxt[0] if len(nxt) == 1 else None
                    if t is not None:
                        end = t.GetEnd() if t.GetStart() == end else t.GetStart()
                cut = [_inside(u, lambda q: p.HitTest(q)) for u in chain]
                cross = [x for _, xs in cut for x in xs]
                if cross:                # (a chain that never leaves the pad is left as it is)
                    L += pcbnew.ToMM((cross[0] - c).EuclideanNorm()) - sum(i for i, _ in cut)
    return L


def _mm(p):
    return pcbnew.ToMM(p.x) - R.O, pcbnew.ToMM(p.y) - R.O


def tune_pair(board, pnet, nnet, cls, tol=0.025, log=print, name=''):
    pc, ncode = board.FindNet(pnet).GetNetCode(), board.FindNet(nnet).GetNetCode()
    for _ in range(40):
        lp, ln = length(board, pc), length(board, ncode)
        d = lp - ln
        if abs(d) <= tol:
            return d
        short, other = (pc, ncode) if d < 0 else (ncode, pc)
        if not bump(board, short, other, cls, abs(d), shape='U' if abs(d) > 0.15 else 'V') and \
                not bump(board, short, other, cls, abs(d), shape='V'):
            log(f'  {name}: skew {d:+.3f} mm left (no room for a bump)')
            return d
    return length(board, pc) - length(board, ncode)


def bump(board, code, partner, cls, need, shape='V'):
    """one bump on the longest straight coupled segment of net `code` that has room, pushed away from the partner.
    shape 'V': trapezoid with 45-degree flanks, adds 0.83 h, h <= 2.5 x the pair gap. shape 'U': vertical sides with
    45-degree chamfers (c = 0.1 mm), adds 2 h - 2.34 c, h <= 4 x the gap and <= 0.8 mm"""
    ts, _ = net_items(board, code)
    pts_, _ = net_items(board, partner)
    cands = []
    for t in ts:
        L = t.GetLayer()
        if L not in LNAME:
            continue
        w, s = GEOM[cls]['out' if L in (pcbnew.F_Cu, pcbnew.B_Cu) else 'inn']
        a, b = _mm(t.GetStart()), _mm(t.GetEnd())
        ln = math.dist(a, b)
        if ln < 0.8:
            continue
        u = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        nrm = (-u[1], u[0])
        side, near = 0, False
        for q in pts_:                                   # partner parallel at the pair pitch?
            if q.GetLayer() != L:
                continue
            c = _mm(q.GetStart())
            off = (c[0] - a[0]) * nrm[0] + (c[1] - a[1]) * nrm[1]
            e = _mm(q.GetEnd())
            lq = math.dist(c, e)
            if min(_seg_dist(c, a, b), _seg_dist(e, a, b), _seg_dist(a, c, e), _seg_dist(b, c, e)) < 1.0:
                near = True
            if lq < 1e-6 or abs(abs(((e[0] - c[0]) * u[0] + (e[1] - c[1]) * u[1]) / lq) - 1) > 1e-3:
                continue
            if abs(abs(off) - (w + s)) < 0.03:
                side = -1 if off > 0 else 1              # bump away from the partner
                break
        if side:
            cands.append((ln, t, a, b, u, nrm, side, w, s, L))
        elif shape == 'U':                               # uncoupled stretch (breakout): either side that clears
            cands += [(ln - 1e-3, t, a, b, u, nrm, sd, w, s, L) for sd in (1, -1)]
    cands.sort(key=lambda c: -c[0])
    cc = 0.1
    for ln, t, a, b, u, nrm, side, w, s, L in cands:
        # U bumps up to 4 x the gap (0.4-0.8 mm): ~0.7 mm long, far below a rise length (~4.5 mm for 30 ps in FR-4),
        # so the local loss of coupling is not seen; V bumps stay within 2.5 x the gap
        hmax = min(4 * s, 0.8) if shape == 'U' else 2.5 * s
        flat = max(3 * w, 0.3)
        if shape == 'U':
            h = min(hmax, (need + 2.34 * cc) / 2)
            h = max(h, 2 * cc + 0.05)
            span = flat + 4 * cc
        else:
            h = min(hmax, need / 0.828)
            h = max(h, 0.05)
            span = 2 * h + flat
        if span + 0.3 > ln:
            continue
        # centred first, then along the segment (0.15 mm from its ends at least: every bump is clearance-checked)
        t0s = [(ln - span) / 2] + [0.15 + k * 0.25 for k in range(int((ln - span - 0.3) / 0.25) + 1)]
        for t0 in t0s:
            P = lambda tt, hh: (a[0] + u[0] * (t0 + tt) + nrm[0] * side * hh, a[1] + u[1] * (t0 + tt) + nrm[1] * side * hh)
            if shape == 'U':
                pts = [P(0, 0), P(cc, cc), P(cc, h - cc), P(2 * cc, h), P(span - 2 * cc, h), P(span - cc, h - cc),
                       P(span - cc, cc), P(span, 0)]
            else:
                pts = [P(0, 0), P(h, h), P(h + flat, h), P(span, 0)]
            if not _free(board, code, partner, L, pts, w):
                continue
            net = t.GetNetname()
            # the pair's 0.09 mm rule, exactly (tracks built off the board for the check)
            if not R.clear_of(board, R.add_track(board, net, LNAME[L], [a] + pts + [b], w, add=False), {partner}, 0.092):
                continue
            if _own_contact(board, code, L, t, [a] + pts + [b], w):
                continue
            R.remove(board, t)
            R.add_track(board, net, LNAME[L], [a] + pts + [b], w)
            return True
    return False
    return False


def _seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _seg_seg(p, q, a, b):
    """distance between segments p-q and a-b (0 where they cross)"""
    o = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
    if o(p, q, a) * o(p, q, b) < 0 and o(a, b, p) * o(a, b, q) < 0:
        return 0.0
    return min(_seg_dist(p, a, b), _seg_dist(q, a, b), _seg_dist(a, p, q), _seg_dist(b, p, q))


def _own_contact(board, code, L, skip, poly, w):
    """the polyline poly (width w on layer L), which replaces track `skip` between the same two ends, touches other
    copper of its own net with its raised part (the pieces off the line through its ends): the signal would take that
    shortcut and the added length would not be there (prune removes it). The net's copper at the two ends is where the
    polyline belongs: a via there, and the first 0.12 mm of a track from there, are left out"""
    a, b = poly[0], poly[-1]
    ln = math.dist(a, b)
    if ln < 1e-6:
        return False
    nrm = (-(b[1] - a[1]) / ln, (b[0] - a[0]) / ln)
    off = lambda p: abs((p[0] - a[0]) * nrm[0] + (p[1] - a[1]) * nrm[1])
    raised = [(p, q) for p, q in zip(poly, poly[1:]) if max(off(p), off(q)) > 0.01]
    ts, vs = net_items(board, code)
    for t in ts:
        if t.m_Uuid.AsString() == skip.m_Uuid.AsString() or t.GetLayer() != L:
            continue
        s0, s1 = _mm(t.GetStart()), _mm(t.GetEnd())
        lt = math.dist(s0, s1)
        for e in (a, b):                 # a track from an end: its first 0.12 mm is the joint, not a shortcut
            if lt > 0 and min(math.dist(s0, e), math.dist(s1, e)) < 0.01:
                if lt <= 0.12:
                    lt = 0.0
                    break
                if math.dist(s0, e) < 0.01:
                    s0 = (s0[0] + (s1[0] - s0[0]) * 0.12 / lt, s0[1] + (s1[1] - s0[1]) * 0.12 / lt)
                else:
                    s1 = (s1[0] + (s0[0] - s1[0]) * 0.12 / lt, s1[1] + (s0[1] - s1[1]) * 0.12 / lt)
                lt = math.dist(s0, s1)
        if lt <= 0:
            continue
        near = (w + pcbnew.ToMM(t.GetWidth())) / 2 + 0.02
        if any(_seg_seg(p, q, s0, s1) < near for p, q in raised):
            return True
    for v in vs:
        c, r = _mm(v.GetPosition()), pcbnew.ToMM(v.GetWidth(L)) / 2
        if min(math.dist(c, a), math.dist(c, b)) < r + 0.05:
            continue
        if any(_seg_dist(c, p, q) < r + w / 2 + 0.02 for p, q in raised):
            return True
    return False


def _free(board, code, partner, L, pts, w):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    win = R.Window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, 0.025)
    # the partner is checked exactly afterwards (bump() with R.clear_of): the bump leaves from its own trace, which
    # runs at the pair gap (0.10-0.20 mm) from the partner
    obs = R.Obstacles(board, win, {code, partner}, w / 2, 0.12, layers=(LNAME[L],))
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.dist(a, b) / 0.02))
        for k in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            if not obs.free(LNAME[L], *win.ij(x, y)):
                return False
    return True


def _clusters(board, code):
    """KiCad's connectivity: the groups of pads of net `code` joined by its copper"""
    board.BuildConnectivity()
    c = board.GetConnectivity()
    its = [p for fp in R.footprints(board) for p in R.pads(fp) if p.GetNetCode() == code] + net_items(board, code)[0] + \
        net_items(board, code)[1]
    uid = {it.m_Uuid.AsString(): it for it in its}
    parent = {u: u for u in uid}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u
    for u, it in uid.items():
        for q in c.GetConnectedItems(it):
            if q.m_Uuid.AsString() in uid:
                parent[find(q.m_Uuid.AsString())] = find(u)
    return sorted(sorted(p.GetParentAsString() + '.' + p.GetNumber() for p in its if isinstance(p, pcbnew.PAD) and
                         find(p.m_Uuid.AsString()) == r) for r in {find(u) for u in uid})


def prune(board, code):
    """copper of net `code` on no shortest pad-to-pad path is removed: a hairpin the breakout untwist leaves (the
    coupled section's end, route_pairs), a track folded back over itself. Such copper is a stub on the line and is
    counted in its length, so it is gone before the lengths are tuned. The copper is cut at every point where other
    copper of the net (or a via) touches it, the pieces form a graph (a via inside a pad is that pad), and what the
    shortest paths from the first pad to the others leave out is removed. Nothing is removed when the graph does not
    reach every pad, or when KiCad's connectivity of the pads changes. Returns the length removed (mm)"""
    ts, vs = net_items(board, code)
    pads = [p for fp in R.footprints(board) for p in R.pads(fp) if p.GetNetCode() == code]
    if len(pads) < 2 or not ts:
        return 0.0
    eps = 0.012
    segs = [(t, t.GetLayer(), _mm(t.GetStart()), _mm(t.GetEnd()), pcbnew.ToMM(t.GetWidth()) / 2) for t in ts]
    vxy = [(_mm(v.GetPosition()), pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu)) / 2) for v in vs]
    ends = {}
    for _, L, a, z, hw in segs:
        ends.setdefault(L, []).extend([(a, hw), (z, hw)])
    pieces = []                          # (track, layer, from, to, half width, s0, s1): s along the track
    for t, L, a, z, hw in segs:
        ln = math.dist(a, z)
        cuts = {0.0, ln}
        if ln > 0:
            u = ((z[0] - a[0]) / ln, (z[1] - a[1]) / ln)
            for p, ph in ends[L] + [(v, 0.0) for v, _ in vxy]:
                s = (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]
                if eps < s < ln - eps and abs((p[0] - a[0]) * u[1] - (p[1] - a[1]) * u[0]) < hw + ph:
                    cuts.add(s)
        else:
            u = (0.0, 0.0)
        cs = sorted(cuts)
        for s0, s1 in zip(cs, cs[1:]):
            pieces.append((t, L, (a[0] + u[0] * s0, a[1] + u[1] * s0), (a[0] + u[0] * s1, a[1] + u[1] * s1), hw, s0, s1))
    nodes = [('via', None, v, r) for v, r in vxy] + [('pad', None, _mm(p.GetPosition()), p) for p in pads]
    alias = {}                           # a via inside a pad is that pad
    for i, (v, _) in enumerate(vxy):
        for j, p in enumerate(pads):
            if p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(v[0] + R.O), pcbnew.FromMM(v[1] + R.O))):
                alias[i] = len(vxy) + j

    def node(L, p, hw):
        for i, (k, nl, q, r) in enumerate(nodes):
            if k == 'via' and math.dist(p, q) <= r + 1e-3:
                return alias.get(i, i)
            if k == 'pad' and r.IsOnLayer(L) and r.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(p[0] + R.O), pcbnew.FromMM(p[1] + R.O))):
                return i
            # ends closer than half a width (copper overlapping by more than half): one width merged ends that only
            # touched, and the pieces between them were removed as off-path, leaving touching joints (D110)
            if k == 'pt' and nl == L and math.dist(p, q) < max(eps, hw):
                return i
        nodes.append(('pt', L, p, None))
        return len(nodes) - 1
    edges, home = {}, {}                 # (i, j) -> [piece index], the shortest first; a piece within one node
    for k, (t, L, a, z, hw, s0, s1) in enumerate(pieces):
        i, j = node(L, a, hw), node(L, z, hw)
        if i != j:
            edges.setdefault((min(i, j), max(i, j)), []).append(k)
        else:
            home[k] = i
    for e in edges.values():
        e.sort(key=lambda k: pieces[k][6] - pieces[k][5])
    adj = {}
    for (i, j), ks in edges.items():
        w = pieces[ks[0]][6] - pieces[ks[0]][5]
        adj.setdefault(i, []).append((j, w))
        adj.setdefault(j, []).append((i, w))
    padn = [len(vxy) + j for j in range(len(pads))]
    dist, prev, q = {padn[0]: 0.0}, {}, [(0.0, padn[0])]
    while q:
        d, i = heapq.heappop(q)
        if d > dist[i]:
            continue
        for j, w in adj.get(i, ()):
            if d + w < dist.get(j, 1e9):
                dist[j], prev[j] = d + w, i
                heapq.heappush(q, (d + w, j))
    if any(i not in dist for i in padn):
        return 0.0
    keep, on = set(), set(padn)
    for i in padn[1:]:
        while i in prev:
            keep.add(edges[(min(i, prev[i]), max(i, prev[i]))][0])
            on.add(prev[i])
            i = prev[i]
    # a piece within a pad or a via forms no loop: it stays where its node is on the paths (the stub into a via's
    # centre is what KiCad's length and the via barrel are counted from); one within a corner goes
    keep |= {k for k, i in home.items() if i in on and nodes[i][0] != 'pt'}
    if len(keep) == len(pieces):
        return 0.0
    before = _clusters(board, code)
    removed, added, cut = [], [], 0.0
    for t, *_ in segs:
        mine = [k for k, pc in enumerate(pieces) if pc[0] is t]
        if all(k in keep for k in mine):
            continue
        runs = []                        # the kept stretches of the track, contiguous pieces joined
        for k in mine:
            s0, s1 = pieces[k][5], pieces[k][6]
            if k in keep:
                if runs and abs(runs[-1][1] - s0) < 1e-9:
                    runs[-1][1] = s1
                else:
                    runs.append([s0, s1])
            else:
                cut += s1 - s0
        a, z = _mm(t.GetStart()), _mm(t.GetEnd())
        ln = math.dist(a, z)
        P = lambda s: (a[0] + (z[0] - a[0]) * s / ln, a[1] + (z[1] - a[1]) * s / ln)
        for s0, s1 in runs:
            added += R.add_track(board, t.GetNetname(), LNAME[t.GetLayer()], [P(s0), P(s1)],
                                 pcbnew.ToMM(t.GetWidth()), locked=t.IsLocked())
        R.remove(board, t)
        removed.append(t)
    left = net_items(board, code)[0]
    for i, (v, it) in enumerate(zip(vxy, vs)):
        # a via the paths do not pass, or that joins fewer than two layers once the copper is gone
        Ls = {t.GetLayer() for t in left for e in (_mm(t.GetStart()), _mm(t.GetEnd())) if math.dist(e, v[0]) <= v[1] + 1e-3}
        Ls |= {L for p in pads if p.HitTest(it.GetPosition()) for L in p.GetLayerSet().CuStack()}
        if alias.get(i, i) not in on or len(Ls) < 2:
            R.remove(board, it)
            removed.append(it)
    if _clusters(board, code) != before:  # (never seen; the graph is cruder than KiCad's copper)
        for t in added:
            R.remove(board, t)
        for t in removed:
            board.Add(t)
        return 0.0
    return cut


def tune_all(board, pairs, log=print):
    """pairs: [(name, P net, N net, class)]; copper off the pad-to-pad path is removed first (prune)"""
    res = []
    for name, p, n, cls in pairs:
        for net in (p, n):
            cut = prune(board, board.FindNet(net).GetNetCode())
            if cut:
                log(f'  {name}: {cut:.3f} mm of {net.split("/")[-1]} off the pad-to-pad path removed')
        for _ in range(3):
            d = tune_pair(board, p, n, cls, log=log, name=name)
            # a bump that touched its own net's copper in a way _own_contact does not see: pruned, tuned again
            cut = sum(prune(board, board.FindNet(net).GetNetCode()) for net in (p, n))
            if not cut:
                break
            log(f'  {name}: {cut:.3f} mm the tuning left off the pad-to-pad path removed')
            d = length(board, board.FindNet(p).GetNetCode()) - length(board, board.FindNet(n).GetNetCode())
        res.append((name, d))
    return res


def pair_length(board, pnet, nnet):
    pc, nc = board.FindNet(pnet).GetNetCode(), board.FindNet(nnet).GetNetCode()
    return (length(board, pc) + length(board, nc)) / 2


def pair_bump(board, pnet, nnet, cls, need, side=None, journal=None):
    """add length to both traces of a pair: a trapezoid detour of the whole pair (45 degree flanks) on a straight
    coupled stretch, clearance-checked. Returns the length added (mm) or 0"""
    pc, nc = board.FindNet(pnet).GetNetCode(), board.FindNet(nnet).GetNetCode()
    tp, _ = net_items(board, pc)
    tn, _ = net_items(board, nc)
    best = []
    for a_t in tp:
        L = a_t.GetLayer()
        if L not in LNAME:
            continue
        w, s = GEOM[cls]['out' if L in (pcbnew.F_Cu, pcbnew.B_Cu) else 'inn']
        pitch = w + s
        a, b = _mm(a_t.GetStart()), _mm(a_t.GetEnd())
        la = math.dist(a, b)
        if la < 2.0:
            continue
        u = ((b[0] - a[0]) / la, (b[1] - a[1]) / la)
        nrm = (-u[1], u[0])
        for c_t in tn:
            if c_t.GetLayer() != L:
                continue
            c, d = _mm(c_t.GetStart()), _mm(c_t.GetEnd())
            lc = math.dist(c, d)
            if lc < 2.0 or abs(abs(((d[0] - c[0]) * u[0] + (d[1] - c[1]) * u[1]) / lc) - 1) > 1e-3:
                continue
            off = (c[0] - a[0]) * nrm[0] + (c[1] - a[1]) * nrm[1]
            if abs(abs(off) - pitch) > 0.03:
                continue
            t0, t1 = sorted(((c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1], (d[0] - a[0]) * u[0] + (d[1] - a[1]) * u[1]))
            lo, hi = max(0.0, t0), min(la, t1)
            if hi - lo > 2.0:
                best.append((hi - lo, a_t, c_t, a, u, nrm, off, lo, hi, w, s, L))
    best.sort(key=lambda x: -x[0])
    for ov, a_t, c_t, a, u, nrm, off, lo, hi, w, s, L in best:
        flat = max(0.5, 4 * w)
        H = min(need / 0.828, 3.0)
        H = max(H, 0.1)
        span = 2 * H + flat
        if span + 1.4 > hi - lo:
            H = max(0.1, ((hi - lo) - 1.4 - flat) / 2)
            span = 2 * H + flat
            if H < 0.1:
                continue
        mid = (a[0] + nrm[0] * off / 2, a[1] + nrm[1] * off / 2)          # centreline through a's offset
        for sgn in ((side,) if side else (1, -1)):
            t_start = lo + ((hi - lo) - span) / 2
            cl = [(mid[0] + u[0] * (t_start - 0.3), mid[1] + u[1] * (t_start - 0.3)),
                  (mid[0] + u[0] * t_start, mid[1] + u[1] * t_start)]
            cl.append((cl[-1][0] + u[0] * H + nrm[0] * sgn * H, cl[-1][1] + u[1] * H + nrm[1] * sgn * H))
            cl.append((cl[-1][0] + u[0] * flat, cl[-1][1] + u[1] * flat))
            cl.append((cl[-1][0] + u[0] * H - nrm[0] * sgn * H, cl[-1][1] + u[1] * H - nrm[1] * sgn * H))
            cl.append((cl[-1][0] + u[0] * 0.3, cl[-1][1] + u[1] * 0.3))
            if not _pair_free(board, pc, nc, L, cl, w + s / 2) or _run_contact(board, a_t, c_t, u, off, cl, w, L):
                continue
            # rebuild both segments: straight - offset bump - straight
            # offset_polyline offsets to the left of travel = -nrm; P lies at mid - nrm*off/2, N at mid + nrm*off/2
            for t, net_t, o in ((a_t, a_t.GetNetname(), off / 2), (c_t, c_t.GetNetname(), -off / 2)):
                s0, s1 = _mm(t.GetStart()), _mm(t.GetEnd())
                if (s1[0] - s0[0]) * u[0] + (s1[1] - s0[1]) * u[1] < 0:
                    s0, s1 = s1, s0
                bump_pts = R.offset_polyline(cl, o)
                R.remove(board, t)
                added = R.add_track(board, net_t, LNAME[L], [s0] + bump_pts + [s1], w)
                if journal is not None:
                    journal.append((t, added))
            return 0.828 * H
    return 0.0


def _coupled_runs(board, pc, nc, cls, min_len=2.0):
    """straight stretches where P and N run parallel at the pair pitch on the same layer, longest first:
    (overlap, P track, N track, a, u, nrm, off, lo, hi, w, s, L) with a = P start, u along P, off = N offset along nrm"""
    tp, _ = net_items(board, pc)
    tn, _ = net_items(board, nc)
    out = []
    for a_t in tp:
        L = a_t.GetLayer()
        if L not in LNAME:
            continue
        w, s = GEOM[cls]['out' if L in (pcbnew.F_Cu, pcbnew.B_Cu) else 'inn']
        a, b = _mm(a_t.GetStart()), _mm(a_t.GetEnd())
        la = math.dist(a, b)
        if la < min_len:
            continue
        u = ((b[0] - a[0]) / la, (b[1] - a[1]) / la)
        nrm = (-u[1], u[0])
        for c_t in tn:
            if c_t.GetLayer() != L:
                continue
            c, d = _mm(c_t.GetStart()), _mm(c_t.GetEnd())
            lc = math.dist(c, d)
            if lc < min_len or abs(abs(((d[0] - c[0]) * u[0] + (d[1] - c[1]) * u[1]) / lc) - 1) > 1e-3:
                continue
            off = (c[0] - a[0]) * nrm[0] + (c[1] - a[1]) * nrm[1]
            if abs(abs(off) - (w + s)) > 0.03:
                continue
            t0, t1 = sorted(((c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1], (d[0] - a[0]) * u[0] + (d[1] - a[1]) * u[1]))
            lo, hi = max(0.0, t0), min(la, t1)
            if hi - lo > min_len:
                out.append((hi - lo, a_t, c_t, a, u, nrm, off, lo, hi, w, s, L))
    out.sort(key=lambda x: -x[0])
    return out


def _run_contact(board, a_t, c_t, u, off, cl, w, L):
    """the two traces a pair detour along centreline cl would give the tracks a_t / c_t touch their own nets' other
    copper (_own_contact)"""
    for t, o in ((a_t, off / 2), (c_t, -off / 2)):
        s0, s1 = _mm(t.GetStart()), _mm(t.GetEnd())
        if (s1[0] - s0[0]) * u[0] + (s1[1] - s0[1]) * u[1] < 0:
            s0, s1 = s1, s0
        if _own_contact(board, t.GetNetCode(), L, t, [s0] + R.offset_polyline(cl, o) + [s1], w):
            return True
    return False


def _replace_pair(board, run, cl, journal=None):
    """replace the coupled stretch `run` by the pair centreline polyline cl (both traces offset from it); journal:
    [(track taken out, tracks put in)] for _undo"""
    ov, a_t, c_t, a, u, nrm, off, lo, hi, w, s, L = run
    for t, o in ((a_t, off / 2), (c_t, -off / 2)):
        net_t = t.GetNetname()
        s0, s1 = _mm(t.GetStart()), _mm(t.GetEnd())
        if (s1[0] - s0[0]) * u[0] + (s1[1] - s0[1]) * u[1] < 0:
            s0, s1 = s1, s0
        pts = R.offset_polyline(cl, o)
        R.remove(board, t)
        added = R.add_track(board, net_t, LNAME[L], [s0] + pts + [s1], w)
        if journal is not None:
            journal.append((t, added))


def _undo(board, journal):
    """the tracks a journal took out back in place of what it put in, if they still clear the other nets"""
    for t, _ in journal:
        own = {t.GetNetCode()} | {a[0].GetNetCode() for _, a in journal if a}
        pts = [_mm(t.GetStart()), _mm(t.GetEnd())]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        win = R.Window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, 0.025)
        obs = R.Obstacles(board, win, own, pcbnew.ToMM(t.GetWidth()) / 2, 0.12, layers=(LNAME[t.GetLayer()],))
        n = max(2, int(math.dist(*pts) / 0.02))
        for k in range(n + 1):
            x, y = pts[0][0] + (pts[1][0] - pts[0][0]) * k / n, pts[0][1] + (pts[1][1] - pts[0][1]) * k / n
            if not obs.free(LNAME[t.GetLayer()], *win.ij(x, y)):
                return False
    for t, added in reversed(journal):
        for a in added:
            R.remove(board, a)
        board.Add(t)
    journal.clear()
    return True


def pair_meander(board, pnet, nnet, cls, need, side=None, journal=None):
    """add length to both traces of a pair with an accordion on a straight coupled stretch: k periods of a U (out by
    A, along F, back by A, along G) with 45-degree chamfered corners, in the pair centreline; the legs of the pair stay
    F = G = 1.0 mm apart (pair-edge gap >= 2.5 x the pair gap). Each period adds 2A - 4 x 0.586 c. Returns mm added"""
    pc, nc = board.FindNet(pnet).GetNetCode(), board.FindNet(nnet).GetNetCode()
    c, F, G = 0.2, 1.0, 1.0
    per = lambda A: 2 * A - 4 * (2 - math.sqrt(2)) * c
    for run in _coupled_runs(board, pc, nc, cls):
        ov, a_t, c_t, a, u, nrm, off, lo, hi, w, s, L = run
        for amax in (1.2, 0.9, 0.7):
            k = max(1, math.ceil(need / per(amax)))
            A = (need / k + 4 * (2 - math.sqrt(2)) * c) / 2
            if A < 2 * c + 0.1:
                A, k = 2 * c + 0.1, 1
            span = k * (F + G) - G + 2 * c + 0.6
            if span + 0.8 > hi - lo:
                continue
            mid = (a[0] + nrm[0] * off / 2, a[1] + nrm[1] * off / 2)
            for sgn in ((side,) if side else (1, -1)):
                t = lo + ((hi - lo) - span) / 2 + c + 0.3
                P = lambda tt, hh: (mid[0] + u[0] * tt + nrm[0] * sgn * hh, mid[1] + u[1] * tt + nrm[1] * sgn * hh)
                cl = [P(t - c - 0.3, 0)]               # straight lead-in / lead-out: the end offsets stay square
                for _ in range(k):
                    cl += [P(t - c, 0), P(t, c), P(t, A - c), P(t + c, A), P(t + F - c, A), P(t + F, A - c),
                           P(t + F, c), P(t + F + c, 0)]
                    t += F + G
                cl.append(P(t - G + c + 0.3, 0))
                if not _pair_free(board, pc, nc, L, cl, w + s / 2) or _run_contact(board, a_t, c_t, u, off, cl, w, L):
                    continue
                L0 = pair_length(board, pnet, nnet)
                _replace_pair(board, run, cl, journal)
                return pair_length(board, pnet, nnet) - L0
    return 0.0


def _pair_free(board, pc, nc, L, cl, half):
    xs, ys = [p[0] for p in cl], [p[1] for p in cl]
    win = R.Window(min(xs) - 1.5, min(ys) - 1.5, max(xs) + 1.5, max(ys) + 1.5, 0.025)
    obs = R.Obstacles(board, win, {pc, nc}, half, 0.13, layers=(LNAME[L],))
    for a, b in zip(cl, cl[1:]):
        n = max(2, int(math.dist(a, b) / 0.02))
        for k in range(n + 1):
            x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
            if not obs.free(LNAME[L], *win.ij(x, y)):
                return False
    return True


def _lengthen(board, p, q, cls, need, journal=None):
    """need mm added to a pair in one accordion (a bump under 0.6 mm); where no straight stretch has room for all of
    it, as much as fits: 70 / 50 / 35 / 20 % of it, so a lane boxed in on its long runs still gets closer (D119).
    Returns mm added"""
    for frac in (1.0, 0.7, 0.5, 0.35, 0.2):
        want = need * frac
        if want < 0.3:
            break
        got = (pair_meander(board, p, q, cls, want, journal=journal) if want > 0.6 else
               pair_bump(board, p, q, cls, want, journal=journal))
        if got:
            return got
    return 0.0


def match_group(board, lanes, cls, tol=0.5, log=print, title='', clock=None):
    """lanes: [(name, P net, N net)]: lengthen the shorter lanes, the clock lane among them, to the longest data
    lane (to the clock as routed, where that is longer, D119), within tol, the one furthest short first. Where the board had no room to bring a data lane up, the clock
    lane's detours are taken out again and it goes to the middle of the data lanes instead (every data lane is sampled
    on the clock)"""
    data = [ln for ln in lanes if ln[0] != clock]
    clk = [ln for ln in lanes if ln[0] == clock]

    def to(lane, target, journal=None):
        n, p, q = lane
        for _ in range(8):
            need = target - pair_length(board, p, q)
            if need <= tol / 2:
                return True
            if not (pair_meander(board, p, q, cls, need, journal=journal) if need > 0.6 else
                    pair_bump(board, p, q, cls, need, journal=journal)):
                return False
        return False
    # a clock routed longer than every data lane: the data lanes go up to it, as far as there is room (D119)
    clk0 = max([pair_length(board, p, q) for _, p, q in clk] or [0.0])
    journal = []
    for _ in range(8):
        Ls = {n: pair_length(board, p, q) for n, p, q in lanes}
        top = max([Ls[n] for n, _, _ in data] + [clk0])
        short = [(top - Ls[n], n, p, q) for n, p, q in lanes if top - Ls[n] > tol]
        if not short:
            break
        progress = False
        for need, n, p, q in sorted(short, reverse=True):
            jr = journal if n == clock else None
            added = _lengthen(board, p, q, cls, need, jr)
            if added:
                progress = True
        if not progress:
            log(f'  {title}: no room to lengthen {[n for _, n, _, _ in short]}')
            break
    Ls = {n: pair_length(board, p, q) for n, p, q in data}
    mid = (min(Ls.values()) + max(Ls.values())) / 2
    for lane in clk:
        Lc = pair_length(board, lane[1], lane[2])
        if Lc > mid + tol / 2 and journal:
            if _undo(board, journal):
                log(f'  {title}: data lanes {min(Ls.values()):.2f}-{max(Ls.values()):.2f} mm, {lane[0]} back to the middle')
            else:
                log(f'  {title}: {lane[0]}\'s detours cannot be taken out again')
        if pair_length(board, lane[1], lane[2]) < mid - tol / 2 and not to(lane, mid):
            log(f'  {title}: no room to lengthen {lane[0]} to {mid:.2f} mm')
    cut = sum(prune(board, board.FindNet(net).GetNetCode()) for _, p, q in lanes for net in (p, q))
    if cut:
        log(f'  {title}: {cut:.3f} mm the matching left off the pad-to-pad paths removed')
    return {n: pair_length(board, p, q) for n, p, q in lanes}
