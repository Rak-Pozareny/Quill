"""GND fan-out before the grid router, for both boards.

Every SMD GND pad gets its own via:
- in the pad, where the board has filled and capped via-in-pad (Board A, JLC 6-layer default) and the via fits inside
  the pad; exposed pads get a grid of vias at 1 mm pitch (a via inside its own pad may sit in another net's pour: the
  pour is cleared around the pad anyway);
- otherwise next to the pad, joined by a short stub (narrower than the pad, so fine-pitch neighbours keep clearance);
  stubs keep out of other nets' pours, which one could cut in two; a pad with no room shares a neighbouring GND pad's
  via, or is left to the grid router (gen/route_a.py routes GND pins with the signals).
front_row_gnd(): the camera connectors' boxed-in front-row GND pins, before the pairs (D60).
"""
import math
import re

import pcbnew

import proute as R


class Fanout:
    def __init__(self, b, via, layers=R.ROUTE_LAYERS, clearance=0.12, in_pad=False, inward=(), special=None,
                 net='GND', log=print):
        """special: {(ref, pad number): callable(fanout, footprint, pad)} for pads handled by hand"""
        self.b, self.via, self.layers, self.clr, self.in_pad = b, via, layers, clearance, in_pad
        self.inward, self.special, self.net, self.log = inward, special or {}, net, log
        self.code = b.FindNet(net).GetNetCode()
        self.placed = [R.to_mm(t.GetPosition()) for t in R.tracks(b) if isinstance(t, pcbnew.PCB_VIA)]
        self.geom = []                    # ('t', layer, pts, width) / ('v', x, y): keepouts, and restore after import

    # -------------------------------------------------------------------------------------------------- primitives
    def add_via(self, x, y):
        R.add_via(self.b, self.net, x, y, *self.via)
        self.placed.append((x, y))
        self.geom.append(('v', x, y))

    def add_track(self, L, pts, w):
        R.add_track(self.b, self.net, L, pts, w)
        self.geom.append(('t', L, pts, w))

    def obstacles(self, c, half, r=2.6, zones=True):
        """zones=True: the other nets' pours are obstacles (a GND stub across one can cut a piece of it off);
        'hull': only the switch-node ones (a via inside its own GND pad cannot cut anything)"""
        win = R.Window(c[0] - r, c[1] - r, c[0] + r, c[1] + r, 0.025)
        return win, R.Obstacles(self.b, win, {self.code}, half, self.clr, via_r=self.via[0] / 2, layers=self.layers,
                                zones=zones, escapes='all')

    def far_from_vias(self, x, y, d):
        return all(math.dist((x, y), q) >= d for q in self.placed)

    # ------------------------------------------------------------------------------------------------------- pads
    def run(self):
        fail, n_in, n_stub, n_share, n_ep, n_bent = [], 0, 0, 0, 0, 0
        # pads that already have their own track (front_row_gnd) are left alone
        ends = {(round(x, 3), round(y, 3)) for t in R.tracks(self.b) if t.GetNetCode() == self.code and
                not isinstance(t, pcbnew.PCB_VIA) for x, y in (R.to_mm(t.GetStart()), R.to_mm(t.GetEnd()))}
        for fp in R.footprints(self.b):
            for p in R.pads(fp):
                if p.GetNetCode() != self.code or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or fp.IsNetTie():
                    continue
                if tuple(round(v, 3) for v in R.to_mm(p.GetPosition())) in ends:
                    continue
                key = (fp.GetReference(), p.GetNumber())
                if key in self.special:
                    self.special[key](self, fp, p)
                    continue
                if self.in_pad and self.via_in_pad(p):
                    n_in += 1
                    continue
                if self.into_ep(fp, p):
                    n_ep += 1
                    continue
                r = self.stub(fp, p)
                if r == 'stub':
                    n_stub += 1
                elif r == 'share':
                    n_share += 1
                elif r == 'bent':
                    n_bent += 1
                else:
                    fail.append(f'{fp.GetReference()}.{p.GetNumber()}')
        self.log(f'{self.net} fan-out: {n_in} pads with via-in-pad, {n_ep} QFN pins into their exposed pad, {n_stub} '
                 f'stub + via, {n_bent} bent stub + via, {n_share} sharing a via, {len(self.placed)} vias in all; '
                 f'no room at {fail}')
        return fail

    def via_in_pad(self, p):
        """via(s) inside the pad where they fit with 0.05 mm of pad copper around them; False when they don't"""
        if any(q.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and q.GetNetCode() == p.GetNetCode() and
               p.HitTest(q.GetPosition()) for q in R.pads(p.GetParentFootprint())):
            return True                           # the footprint's own thermal vias (exposed pads) do it already
        bb = p.GetBoundingBox()
        w, h = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        d = self.via[0]
        if min(w, h) < d + 0.1:
            return False
        c = R.to_mm(p.GetPosition())
        if min(w, h) < 1.5:
            spots = [c]
        else:                                     # exposed pad: grid at 1 mm pitch, inset by the via radius + 0.1
            nx, ny = max(1, int((w - d - 0.2) / 1.0) + 1), max(1, int((h - d - 0.2) / 1.0) + 1)
            spots = [(c[0] + (i - (nx - 1) / 2) * 1.0, c[1] + (j - (ny - 1) / 2) * 1.0)
                     for i in range(nx) for j in range(ny)]
        win, obs = self.obstacles(c, 0.05, r=max(w, h) / 2 + 1.5, zones='hull')
        ok = []
        for x, y in spots:
            inside = all(p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(R.O + x + d / 2 * dx), pcbnew.FromMM(R.O + y + d / 2 * dy)))
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7, 0.7), (-0.7, 0.7), (0.7, -0.7), (-0.7, -0.7)))
            if inside and obs.via_free(*win.ij(x, y)) and self.far_from_vias(x, y, self.via[1] + 0.25):
                ok.append((x, y))
        if not ok:
            return False
        for x, y in ok:
            self.add_via(x, y)
        return True

    def into_ep(self, fp, p):
        """a GND pin of a package whose exposed pad is GND: a stub along the pin's own axis into the exposed pad, no
        via (pins that do not face the exposed pad are left to the other methods)"""
        bb = p.GetBoundingBox()
        pw, ph = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
        eps = [q for q in R.pads(fp) if q.GetNetCode() == self.code and q.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and
               pcbnew.ToMM(q.GetBoundingBox().GetWidth()) * pcbnew.ToMM(q.GetBoundingBox().GetHeight()) > 6 * pw * ph
               and min(pcbnew.ToMM(q.GetBoundingBox().GetWidth()), pcbnew.ToMM(q.GetBoundingBox().GetHeight())) > 1.2]
        if not eps:
            return False
        e = eps[0]
        c = R.to_mm(p.GetPosition())
        eb = e.GetBoundingBox()
        ex0, ey0 = pcbnew.ToMM(eb.GetX()) - R.O, pcbnew.ToMM(eb.GetY()) - R.O
        ex1, ey1 = ex0 + pcbnew.ToMM(eb.GetWidth()), ey0 + pcbnew.ToMM(eb.GetHeight())
        if pw > ph:                               # pin along x: must face the pad's left / right side
            if not ey0 + 0.2 < c[1] < ey1 - 0.2:
                return False
            x = ex0 + 0.3 if c[0] < ex0 else ex1 - 0.3
            z = (x, c[1])
        else:
            if not ex0 + 0.2 < c[0] < ex1 - 0.2:
                return False
            y = ey0 + 0.3 if c[1] < ey0 else ey1 - 0.3
            z = (c[0], y)
        if math.dist(c, z) > 2.5:
            return False
        w = max(0.1, min(0.25, round(0.8 * min(pw, ph), 2)))
        L = 'B' if p.IsOnLayer(pcbnew.B_Cu) else 'F'
        win, obs = self.obstacles(c, w / 2)
        n = max(2, int(math.dist(c, z) / 0.02))
        if not all(obs.free(L, *win.ij(c[0] + (z[0] - c[0]) * i / n, c[1] + (z[1] - c[1]) * i / n)) for i in range(n + 1)):
            return False
        self.add_track(L, [c, z], w)
        return True

    def bent(self, c, L, w, win, obs, ok_spot):
        """shortest stub on the pad's layer (8 directions) to the nearest legal via spot; None when there is none"""
        import heapq
        s = win.ij(*c)
        dist, prev = {s: 0.0}, {}
        h = [(0.0, s)]
        while h:
            d, u = heapq.heappop(h)
            if d > dist.get(u, 1e9) or d * win.res > 2.4:
                continue
            x, y = win.xy(*u)
            if d * win.res > self.via[0] / 2 + 0.05 and ok_spot(x, y) and obs.via_free(*u) and \
                    self.far_from_vias(x, y, self.via[0] + 0.2):
                path = [u]
                while path[-1] in prev:
                    path.append(prev[path[-1]])
                pts = [c] + [win.xy(*q) for q in reversed(path)][1:]
                # line-of-sight smoothing: from each kept point straight to the farthest point it sees free
                def clear(a, z):
                    n = max(2, int(math.dist(a, z) / 0.02))
                    return all(obs.free(L, *win.ij(a[0] + (z[0] - a[0]) * t / n, a[1] + (z[1] - a[1]) * t / n)) or
                               math.dist((a[0] + (z[0] - a[0]) * t / n, a[1] + (z[1] - a[1]) * t / n), c) <= 0.05
                               for t in range(n + 1))
                keep, k = [pts[0]], 0
                while k < len(pts) - 1:
                    m = next(m for m in range(len(pts) - 1, k, -1) if m == k + 1 or clear(pts[k], pts[m]))
                    keep.append(pts[m])
                    k = m
                return keep
            for di, dj in R.DIRS:
                v = (u[0] + di, u[1] + dj)
                if not obs.free(L, *v) and math.dist(win.xy(*v), c) > 0.05:
                    continue
                nd = d + (1.4142 if di and dj else 1.0)
                if nd < dist.get(v, 1e9):
                    dist[v], prev[v] = nd, u
                    heapq.heappush(h, (nd, v))
        return None

    def stub(self, fp, p):
        c = R.to_mm(p.GetPosition())
        L = 'B' if p.IsOnLayer(pcbnew.B_Cu) else 'F'
        bb = p.GetBoundingBox()
        w = max(0.1, min(0.3, round(0.65 * pcbnew.ToMM(min(bb.GetWidth(), bb.GetHeight())), 2)))
        win, obs = self.obstacles(c, w / 2)
        pads_bb = None
        for q in R.pads(fp):                       # the part's numbered pads (connector mounting tabs left out)
            if not q.GetNumber().isdigit() and q.GetNumber() not in (p.GetNumber(),):
                continue
            qb = q.GetBoundingBox()
            qq = [pcbnew.ToMM(v) - R.O for v in (qb.GetX(), qb.GetY(), qb.GetRight(), qb.GetBottom())]
            pads_bb = qq if pads_bb is None else [min(pads_bb[0], qq[0]), min(pads_bb[1], qq[1]),
                                                  max(pads_bb[2], qq[2]), max(pads_bb[3], qq[3])]

        want_in = False

        def ok_spot(x, y):          # connectors in `inward`: between the pad rows first; otherwise outside its pads
            ins = pads_bb[0] < x < pads_bb[2] and pads_bb[1] < y < pads_bb[3]
            return ins if want_in else not ins

        def line_free(a, z):
            n = max(2, int(math.dist(a, z) / 0.02))
            return all(obs.free(L, *win.ij(a[0] + (z[0] - a[0]) * i / n, a[1] + (z[1] - a[1]) * i / n))
                       for i in range(n + 1))
        r0 = self.via[0] / 2 + 0.1
        for want_in in ((True, False) if fp.GetReference() in self.inward else (False,)):
            for k in range(40):
                r = r0 + 0.05 * k
                for a in range(16):
                    x, y = c[0] + r * math.cos(a * math.pi / 8), c[1] + r * math.sin(a * math.pi / 8)
                    if ok_spot(x, y) and obs.via_free(*win.ij(x, y)) and self.far_from_vias(x, y, self.via[0] + 0.2) \
                            and line_free(c, (x, y)):
                        self.add_track(L, [c, (x, y)], w)
                        self.add_via(x, y)
                        return 'stub'
        for want_in in ((True, False) if fp.GetReference() in self.inward else (False,)):
            pts = self.bent(c, L, w, win, obs, ok_spot)
            if pts:
                self.add_track(L, pts, w)
                self.add_via(*pts[-1])
                return 'bent'
        for q in sorted(self.placed, key=lambda q: math.dist(c, q)):          # share a neighbouring GND pad's via
            if math.dist(c, q) > 1.6:
                break
            if line_free(c, q):
                self.add_track(L, [c, q], w)
                return 'share'
        return None

    # --------------------------------------------------------------------------------- autorouter file and import
    def strip(self, dsn, clr=0.13):
        """take the net out of a Specctra design file (see the module docstring)"""
        t = open(dsn).read()
        net = re.escape(self.net)
        t, n = re.subn(r'\(net ' + net + r'\s*\(pins[^)]*\)\s*\)', '', t)
        assert n == 1, f'{self.net} not in {dsn}'
        t = re.sub(r'\n\s*\((wire|via) [^\n]*\(net ' + net + r'\)\(type [a-z]+\)\)', '', t)
        k = t.index('(network')                                        # the net in class lists (names may hold '(')
        t = t[:k] + re.sub(r'(?<=\s)' + net + r'(?=[\s)])', '', t[k:])
        while True:                                                   # planes of the net (balanced parentheses)
            k = t.find(f'(plane {self.net} ')
            if k < 0:
                break
            depth, j = 0, k
            while True:
                depth += {'(': 1, ')': -1}.get(t[j], 0)
                j += 1
                if depth == 0:
                    break
            t = t[:k] + t[j:]

        def xy(x, y):
            return f'{(x + R.O) * 1000:.0f} {-(y + R.O) * 1000:.0f}'
        # every track and via of the net now on the board (fan-out, stitching, pours' via arrays), saved for restore()
        self.saved = []
        for it in R.tracks(self.b):
            if it.GetNetCode() != self.code:
                continue
            if isinstance(it, pcbnew.PCB_VIA):
                self.saved.append(('v', *R.to_mm(it.GetPosition()), pcbnew.ToMM(it.GetWidth(pcbnew.F_Cu)),
                                   pcbnew.ToMM(it.GetDrillValue())))
            elif math.dist(R.to_mm(it.GetStart()), R.to_mm(it.GetEnd())) > 1e-3:
                self.saved.append(('t', it.GetLayerName(), [R.to_mm(it.GetStart()), R.to_mm(it.GetEnd())],
                                   pcbnew.ToMM(it.GetWidth())))
        keep = []
        for g in self.saved:
            if g[0] == 'v':
                r = g[3] / 2 + clr
                pts = [(g[1] + r * math.cos(k * math.pi / 8), g[2] + r * math.sin(k * math.pi / 8)) for k in range(16)]
                layer = 'signal'
            else:
                (ax, ay), (bx, by) = g[2]
                h = g[3] / 2 + clr
                ln = math.hypot(bx - ax, by - ay) or 1e-6
                ux, uy = (bx - ax) / ln, (by - ay) / ln
                nx, ny = -uy, ux
                pts = [(ax - ux * h + nx * h, ay - uy * h + ny * h), (bx + ux * h + nx * h, by + uy * h + ny * h),
                       (bx + ux * h - nx * h, by + uy * h - ny * h), (ax - ux * h - nx * h, ay - uy * h - ny * h)]
                layer = g[1]
            keep.append(f'    (keepout "" (polygon {layer} 0  ' + '  '.join(xy(*p) for p in pts) + '))')
        k = t.index('\n    (via "', t.index('(structure'))           # after the layers, with the board's own keepouts
        t = t[:k] + '\n' + '\n'.join(keep) + t[k:]
        open(dsn, 'w').write(t)

    def restore(self):
        """after the session import: re-add the net's tracks and vias saved by strip() if the import dropped them.
        Returns the number of vias re-added"""
        have = {(round(x, 3), round(y, 3)) for x, y in (R.to_mm(t.GetPosition()) for t in R.tracks(self.b)
                                                       if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == self.code)}
        vias = [g for g in self.saved if g[0] == 'v']
        missing = [g for g in vias if (round(g[1], 3), round(g[2], 3)) not in have]
        tracks_too = len(missing) == len(vias)            # the import replaced every track and via
        for g in missing:
            R.add_via(self.b, self.net, g[1], g[2], g[3], g[4])
        if tracks_too:
            for g in self.saved:
                if g[0] == 't':
                    R.add_track(self.b, self.net, {'F.Cu': 'F', 'In2.Cu': 'In2', 'In3.Cu': 'In3', 'B.Cu': 'B'}[g[1]],
                                g[2], g[3])
        return len(missing)


def front_row_gnd(b, pads, via, reaches=(3.6, 3.2, 4.0, 2.8), clearance=0.15, net='GND', log=print, toward=None):
    """Two-row staggered connectors whose rear-row signal traces leave between the front-row pads (FH35C, D38): a
    front-row GND pad is then boxed in by the two traces passing it, and the differential pairs that start right after
    the front row leave it no way out either. Before the pairs are routed, each such pad gets a stub straight out
    along the pin (away from the connector body), between the two pairs on either side, to a via past the pairs'
    launch points (the first of `reaches` mm past the pad centre that is free); the pairs bend around the via.
    pads: {connector ref: [pad numbers]}, the front-row GND pads that are boxed in this way.
    toward: {connector ref: (side, reaches)} for a single-row connector whose GND pins sit between pairs (the display
    FPC, D118): the pins leave along x toward side (+1 / -1), the via at the first free reach.
    The via must clear every copper layer (a through via), the stub only the connector's layer: with the via checked on
    the connector's layer alone, J704.4's landed 0.08 mm from the Wi-Fi U.FL pad on the back (third D119 route)"""
    code = b.FindNet(net).GetNetCode()
    n, fail = 0, []
    for ref, nums in pads.items():
        fp = b.FindFootprintByReference(ref)
        L = 'B' if fp.IsFlipped() else 'F'
        if toward and ref in toward:
            sgn, rs = toward[ref]
            row = [p for p in R.pads(fp) if p.GetNumber() in nums]
        else:
            c = R.to_mm(fp.GetPosition())
            cols = {}                               # pad columns (the pins leave along x)
            for p in R.pads(fp):
                q = R.to_mm(p.GetPosition())
                cols.setdefault(round(q[0], 2), []).append(p)
            if len(cols) < 2:
                continue
            xs = sorted(cols)
            front = xs[-1] if abs(xs[-1] - c[0]) >= abs(xs[0] - c[0]) else xs[0]
            sgn = 1 if front > c[0] else -1
            row, rs = cols[front], reaches
        for p in row:
            if p.GetNetCode() != code or p.GetNumber() not in nums:
                continue
            x, y = R.to_mm(p.GetPosition())
            r = max(rs)
            win = R.Window(x - 1.5 - r, y - 1.5, x + 1.5 + r, y + 1.5, 0.025)
            obs = R.Obstacles(b, win, {code}, 0.05, clearance, via_r=via[0] / 2, zones=False)
            for reach in rs:
                v = (x + sgn * reach, y)
                k = max(2, int(reach / 0.02))
                if obs.via_free(*win.ij(*v)) and \
                        all(obs.free(L, *win.ij(x + sgn * reach * i / k, y)) for i in range(k + 1)):
                    R.add_track(b, net, L, [(x, y), v], 0.1)
                    R.add_via(b, net, v[0], v[1], *via)
                    n += 1
                    break
            else:
                fail.append(f'{ref}.{p.GetNumber()}')
    log(f'{net}: {n} front-row connector pads given a stub + via before the pairs; no room at {fail}')
    return fail
