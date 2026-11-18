"""Grid router with negotiated congestion (PathFinder), for whatever the pre-routing leaves open.

    g = Grid(board, rules)            # static copper rasterised once
    r = Router(g, conns)              # conns: [(net, (x, y, layer|None), (x, y, layer|None))]
    r.run()                           # rip-up and re-route until no two nets share a cell
    r.commit()                        # tracks and vias onto the board

Geometry: square cells of `res` mm. Every static copper item (pads, pre-routed tracks and vias, pours, net-tie copper,
holes, keepouts, the board edge) is rasterised with KiCad's own shape outlines, inflated by its clearance + the
default half-width + `margin` (rounding of the rasterisation), so a track centred on free cells keeps the clearance
as KiCad's DRC measures it: paths run on cell centres, and a short stub inside the item's own copper joins the pad,
track end or via a path starts or ends on. Routed nets are rasterised the same way into count rasters,
which the negotiation loop uses: overlap costs (present factor) and history costs grow until no overlap is left.
The search itself is C (gen/groute.c): A* over (layer, cell, direction), 45-degree turns cheap, 90 dear, vias.
"""
import array
import ctypes
import json
import math
import os
import subprocess
import tempfile

import pcbnew

import proute as R

HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None


def lib():
    global _LIB
    if _LIB is None:
        import hashlib
        src = os.path.join(HERE, 'groute.c')
        tag = hashlib.sha1(open(src, 'rb').read()).hexdigest()[:12]
        so = os.path.join(HERE, '..', 'build', f'libgroute-{tag}.so')   # per source version: a running process
        os.makedirs(os.path.dirname(so), exist_ok=True)                  # keeps the library it has mapped
        if not os.path.exists(so):
            subprocess.run(['gcc', '-O2', '-shared', '-fPIC', '-o', so + '.tmp', src, '-lm'], check=True)
            os.replace(so + '.tmp', so)
        _LIB = ctypes.CDLL(so)
        P32, P16, PF = ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_float)
        _LIB.fill_poly.argtypes = [P32, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double, ctypes.c_double,
                                   ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int32]
        _LIB.mark_capsule.argtypes = [P16, ctypes.c_int, ctypes.c_int, ctypes.c_double, ctypes.c_double,
                                      ctypes.c_double] + [ctypes.c_double] * 5 + [ctypes.c_int]
        _LIB.astar.argtypes = ([ctypes.c_int] * 3 + [ctypes.POINTER(P32), P32, ctypes.POINTER(P16), P16,
                                                    ctypes.POINTER(PF), PF, ctypes.c_int32] +
                               [ctypes.c_int] * 4 + [ctypes.POINTER(ctypes.c_double), P32, ctypes.c_int, P32,
                                                     ctypes.c_int, P32, ctypes.c_int, P32, ctypes.c_int,
                                                     P32, ctypes.c_int] +
                               [ctypes.c_double] * 4 + [ctypes.c_int, ctypes.c_long, ctypes.c_int, ctypes.c_long, P32,
                                                        ctypes.c_int])
        _LIB.astar.restype = ctypes.c_int
    return _LIB


def _buf(typ, n):
    a = array.array(typ, bytes(n * array.array(typ).itemsize))
    ct = {'i': ctypes.c_int32, 'H': ctypes.c_uint16, 'f': ctypes.c_float}[typ]
    return a, (ct * n).from_buffer(a)


class Rules:
    """layers: routing layer names; width_of(net, layer), clearance_of(net); h_def / c_def: the default class"""
    def __init__(self, layers, via, width_of, clearance_of, h_def, c_def, hole_clr=0.2, pth_clr=0.28, npth_clr=0.2,
                 hole_to_hole=0.2, edge=0.2, res=0.05, margin=0.04, skip_zone_nets=(), via_in_pad=False, neck=1.0,
                 zone_via_cost=2.0, layer_cost=None, full_states=48_000_000, keep_width=None):
        """full_states: A* windows with at most this many (cell, direction) labels search them all (exact turn
        costs); larger ones use one label per cell (C core). neck: a net wider than the default class runs at the
        default width this far from its ends (fine-pitch pins), except the nets for which keep_width(net) is true
        (impedance-controlled: their width is a DRC rule)"""
        self.__dict__.update(locals())
        del self.__dict__['self']


class Grid:
    def __init__(self, b, rules, log=print, window=None, soft=0.0, soft_nets=()):
        """window: (x0, y0, x1, y1) mm, a part of the board only (a fine local pass). soft: the router's own (unlocked)
        tracks and vias, and the locked ones of the nets soft_nets, do not block; their cells cost this much extra
        per step instead (rip-up and re-route)"""
        self.b, self.r, self.log, self.soft, self.soft_nets = b, rules, log, soft, set(soft_nets)
        if window:
            self.x0, self.y0 = window[0], window[1]
            self.nx = int((window[2] - window[0]) / rules.res) + 1
            self.ny = int((window[3] - window[1]) / rules.res) + 1
        else:
            bb = b.GetBoardEdgesBoundingBox()
            self.x0, self.y0 = pcbnew.ToMM(bb.GetX()) - R.O - 0.5, pcbnew.ToMM(bb.GetY()) - R.O - 0.5
            self.nx = int((pcbnew.ToMM(bb.GetWidth()) + 1.0) / rules.res) + 1
            self.ny = int((pcbnew.ToMM(bb.GetHeight()) + 1.0) / rules.res) + 1
        self.layers = list(rules.layers)
        self.nl = len(self.layers)
        n = self.nx * self.ny
        self.st_t = [_buf('i', n) for _ in self.layers]
        self.st_v = _buf('i', n)
        self.dy_t = [_buf('H', n) for _ in self.layers]
        self.dy_v = _buf('H', n)
        self.hist = [_buf('f', n) for _ in self.layers]
        self.hist_v = _buf('f', n)
        self._static()

    # ---------------------------------------------------------------------------------------------------- helpers
    def ij(self, x, y):
        return int((x - self.x0) / self.r.res), int((y - self.y0) / self.r.res)

    def xy(self, i, j):
        return self.x0 + (i + 0.5) * self.r.res, self.y0 + (j + 0.5) * self.r.res

    def _fill(self, ct, ps, val):
        """scan-line fill of a polygon set; holes are honoured by fracturing first (a hole joined to its outline by a
        zero-width slit fills correctly with the even-odd rule)"""
        L = lib()
        if any(ps.HoleCount(k) for k in range(ps.OutlineCount())):
            ps = ps.CloneDropTriangulation()
            ps.Fracture()
        for k in range(ps.OutlineCount()):
            o = ps.Outline(k)
            pts = [c for i in range(o.PointCount()) for c in R.to_mm(o.CPoint(i))]
            arr = (ctypes.c_double * len(pts))(*pts)
            L.fill_poly(ct, self.nx, self.ny, self.x0, self.y0, self.r.res, arr, len(pts) // 2, val)

    def cdef(self, net):
        return max(self.r.c_def, self.r.clearance_of(net)) if net else self.r.c_def

    # ----------------------------------------------------------------------------------------------- static copper
    def _static(self):
        r, b = self.r, self.b
        vr = r.via[0] / 2
        items = []
        for fp in R.footprints(b):
            items += list(R.pads(fp))
            items += list(fp.Zones())
            g = fp.GraphicalItems()
            for k in range(len(g)):
                it = g[k].Cast()
                if isinstance(it, pcbnew.PCB_SHAPE) and it.IsOnCopperLayer():
                    if fp.IsNetTie():
                        self._net_tie(fp, it)
                    else:
                        items.append(it)
        items += R.tracks(b)
        items += [z for z in b.Zones()]
        pads = [p for fp in R.footprints(b) for p in R.pads(fp) if p.GetNetCode() > 0]
        zone_cells = _buf('i', self.nx * self.ny)          # pours of other nets: vias allowed there, at a cost
        if self.soft:
            soft_t, soft_v = [_buf('i', self.nx * self.ny) for _ in self.layers], _buf('i', self.nx * self.ny)
        for it in items:
            net = it.GetNetCode() if hasattr(it, 'GetNetCode') else 0
            netname = it.GetNetname() if hasattr(it, 'GetNetname') else ''
            val = net if net > 0 else -1
            c = self.cdef(netname)
            st_t, st_v = self.st_t, self.st_v
            if self.soft and isinstance(it, pcbnew.PCB_TRACK) and (not it.IsLocked() or netname in self.soft_nets):
                st_t, st_v = soft_t, soft_v
            if isinstance(it, pcbnew.ZONE):
                if it.GetIsRuleArea():
                    for li, L in enumerate(self.layers):
                        if it.IsOnLayer(R.LAYER[L]) and it.GetDoNotAllowTracks():
                            ps = it.Outline().CloneDropTriangulation()
                            ps.Inflate(R.nm(r.h_def + r.margin), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, R.MAXERR)
                            self._fill(self.st_t[li][1], ps, -1)
                    if it.GetDoNotAllowVias() and any(it.IsOnLayer(R.LAYER[L]) for L in self.layers):
                        ps = it.Outline().CloneDropTriangulation()
                        ps.Inflate(R.nm(vr + r.margin), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, R.MAXERR)
                        self._fill(self.st_v[1], ps, -1)
                    continue
                if netname.split('/')[-1] in r.skip_zone_nets:
                    continue
            for li, L in enumerate(self.layers):
                lid = R.LAYER[L]
                if not it.IsOnLayer(lid):
                    continue
                smd = isinstance(it, pcbnew.PAD) and it.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
                if isinstance(it, pcbnew.ZONE):
                    # a pour is filled around everything else: it blocks tracks on its layer, except for a 0.5 mm
                    # escape around each other-net pad it covers; vias may go through it (with a cost, below)
                    rad = c + r.h_def + r.margin
                    ps = it.Outline().CloneDropTriangulation()
                    zb = it.GetBoundingBox()
                    zb.Inflate(R.nm(rad + 0.6))                 # pads just outside the outline count too
                    holes = pcbnew.SHAPE_POLY_SET()
                    for p in pads:
                        if p.GetNetCode() != net and p.IsOnLayer(lid) and zb.Intersects(p.GetBoundingBox()):
                            p.TransformShapeToPolygon(holes, lid, R.nm(0.5 + rad), R.MAXERR, pcbnew.ERROR_OUTSIDE)
                    if holes.OutlineCount():
                        holes.Simplify()
                        ps.BooleanSubtract(holes)
                    ps.Inflate(R.nm(rad), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, R.MAXERR)
                    self._fill(self.st_t[li][1], ps, val)
                    # switch-node pours, and the CM5_VIN pour the display breakout vias pass (its only other-net vias
                    # are those; router vias there cut U201's output pins off it, D82): no other net's via inside
                    if it.GetZoneName().endswith(('(hull)', '(vias pass)')):
                        pv = it.Outline().CloneDropTriangulation()
                        pv.Inflate(R.nm(c + vr + r.margin), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, R.MAXERR)
                        if it.GetZoneName().endswith('(vias pass)'):
                            # another net's pad inside it keeps a way out: that net's via within 0.6 mm of the pad
                            near = pcbnew.SHAPE_POLY_SET()
                            for p in pads:
                                if p.GetNetCode() != net and p.IsOnLayer(lid) and zb.Intersects(p.GetBoundingBox()):
                                    p.TransformShapeToPolygon(near, lid, R.nm(0.6 + vr), R.MAXERR, pcbnew.ERROR_OUTSIDE)
                            if near.OutlineCount():
                                near.Simplify()
                                pv.BooleanSubtract(near)
                        self._fill(self.st_v[1], pv, val)
                    else:
                        self._fill(zone_cells[1], it.Outline().CloneDropTriangulation(), 1)
                    continue
                # a via's hole keeps the PTH-hole clearance from a plated-through pad's copper (KiCad applies the
                # PTH rule both ways)
                pth = isinstance(it, pcbnew.PAD) and it.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                vrad = max(c + vr, r.pth_clr + r.via[1] / 2) if pth else c + vr
                for dst, rad, v in ((st_t[li][1], c + r.h_def + r.margin, val),
                                    (st_v[1], vrad + r.margin, val if (r.via_in_pad or not smd) else -1)):
                    ps = pcbnew.SHAPE_POLY_SET()
                    it.TransformShapeToPolygon(ps, lid, R.nm(rad), R.MAXERR, pcbnew.ERROR_OUTSIDE)
                    self._fill(dst, ps, v)
            # holes: drill clearance on every layer, hole to hole for vias
            if isinstance(it, (pcbnew.PAD, pcbnew.PCB_VIA)) and it.HasHole():
                if isinstance(it, pcbnew.PCB_VIA):
                    hc, hv = r.hole_clr, val
                elif it.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    hc, hv = r.npth_clr, -1
                else:
                    hc, hv = r.pth_clr, val
                for li in range(self.nl):
                    self._fill(st_t[li][1], R.hole_poly(it, hc + r.h_def + r.margin), hv)
                # vias: hole to hole for every net, and the hole clearance to the via copper of other nets
                h2h = r.hole_to_hole + r.via[1] / 2
                if hc + vr > h2h:
                    self._fill(st_v[1], R.hole_poly(it, hc + vr + r.margin), hv)
                self._fill(st_v[1], R.hole_poly(it, h2h + r.margin), -1)
        if self.soft:                                       # (own-net cells are free anyway: a small extra cost)
            for s, h in [(soft_t[li][0], self.hist[li][0]) for li in range(self.nl)] + [(soft_v[0], self.hist_v[0])]:
                for idx in [k for k, v in enumerate(s) if v]:
                    h[idx] += self.soft
        hv = self.hist_v[0]
        zc = zone_cells[0]
        for idx in range(self.nx * self.ny):
            if zc[idx]:
                hv[idx] += r.zone_via_cost
        # board edge (and its cut-outs): outside the outline shrunk by edge clearance is blocked
        outl = pcbnew.SHAPE_POLY_SET()
        b.GetBoardPolygonOutlines(outl, False)
        for dst_list, rad in (([s[0] for s in self.st_t], r.edge + r.h_def + r.margin), ([self.st_v[0]], r.edge + vr + r.margin)):
            inside = _buf('i', self.nx * self.ny)
            o2 = outl.CloneDropTriangulation()
            o2.Deflate(R.nm(rad), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, R.MAXERR)
            for k in range(o2.OutlineCount()):
                self._fill_ring(inside[1], o2.Outline(k), 1)
                for h in range(o2.HoleCount(k)):
                    self._fill_ring(inside[1], o2.Hole(k, h), 2)       # holes: 1 + 2 -> -1 (blocked), see below
            ins = inside[0]
            out = [idx for idx in range(self.nx * self.ny) if ins[idx] != 1]
            for dst in dst_list:
                for idx in out:
                    dst[idx] = -1
        self.log(f'grid {self.nx} x {self.ny} x {self.nl} layers at {r.res} mm')

    def _net_tie(self, fp, shape):
        """a net tie's copper bridge belongs to both nets: each half (split at the perpendicular bisector of the two
        pads) is owned by the nearer pad's net, so each side stays reachable from its own net only"""
        r = self.r
        pads = [p for p in R.pads(fp) if p.GetNetCode() > 0]
        if len(pads) != 2:
            return
        (ax, ay), (bx, by) = R.to_mm(pads[0].GetPosition()), R.to_mm(pads[1].GetPosition())
        mx, my = (ax + bx) / 2, (ay + by) / 2
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        ux, uy, nx, ny = dx / L, dy / L, -dy / L, dx / L
        big = 50.0
        for li, Ln in enumerate(self.layers):
            lid = R.LAYER[Ln]
            if not shape.IsOnLayer(lid):
                continue
            for p, sgn in ((pads[0], -1), (pads[1], 1)):
                half = pcbnew.SHAPE_POLY_SET()
                half.NewOutline()
                corners = [(mx + nx * big, my + ny * big), (mx - nx * big, my - ny * big),
                           (mx - nx * big + sgn * ux * big, my - ny * big + sgn * uy * big),
                           (mx + nx * big + sgn * ux * big, my + ny * big + sgn * uy * big)]
                for cx, cy in corners:
                    half.Append(R.nm(R.O + cx), R.nm(R.O + cy))
                for dst, rad in ((self.st_t[li][1], self.cdef(p.GetNetname()) + r.h_def + r.margin),
                                 (self.st_v[1], self.cdef(p.GetNetname()) + r.via[0] / 2 + r.margin)):
                    ps = pcbnew.SHAPE_POLY_SET()
                    shape.TransformShapeToPolygon(ps, lid, R.nm(rad), R.MAXERR, pcbnew.ERROR_OUTSIDE)
                    ps.BooleanIntersection(half)
                    self._fill(dst, ps, p.GetNetCode())

    def _fill_ring(self, ct, ring, val):
        pts = [c for i in range(ring.PointCount()) for c in R.to_mm(ring.CPoint(i))]
        arr = (ctypes.c_double * len(pts))(*pts)
        lib().fill_poly(ct, self.nx, self.ny, self.x0, self.y0, self.r.res, arr, len(pts) // 2, val)

    # -------------------------------------------------------------------------------------------- dynamic copper
    def mark(self, path, net, delta):
        """add / remove a routed path (list of (l, i, j)) in the count rasters"""
        r = self.r
        L = lib()
        c = self.cdef(net)
        vr = r.via[0] / 2
        for seg in self.segments(path):
            if seg[0] == 'via':
                _, i, j = seg
                x, y = self.xy(i, j)
                for li in range(self.nl):
                    L.mark_capsule(self.dy_t[li][1], self.nx, self.ny, self.x0, self.y0, r.res, x, y, x, y,
                                   vr + c + r.h_def + r.margin, delta)
                L.mark_capsule(self.dy_v[1], self.nx, self.ny, self.x0, self.y0, r.res, x, y, x, y,
                               vr + c + vr + r.margin, delta)
            else:
                _, li, (i0, j0), (i1, j1) = seg
                (ax, ay), (bx, by) = self.xy(i0, j0), self.xy(i1, j1)
                h = r.width_of(net, self.layers[li]) / 2
                L.mark_capsule(self.dy_t[li][1], self.nx, self.ny, self.x0, self.y0, r.res, ax, ay, bx, by,
                               h + c + r.h_def + r.margin, delta)
                L.mark_capsule(self.dy_v[1], self.nx, self.ny, self.x0, self.y0, r.res, ax, ay, bx, by,
                               h + c + vr + r.margin, delta)

    def block_vias_near(self, path):
        """keep other vias of the same net out of hole-to-hole distance of this path's vias (the via's own cell stays
        open: a later connection may share it). Returns the (index, old value) list for unblock()"""
        r = self.r
        rad = r.via[1] + r.hole_to_hole + r.margin
        k = int(math.ceil(rad / r.res))
        st = self.st_v[0]
        saved = []
        for seg in self.segments(path):
            if seg[0] != 'via':
                continue
            _, i, j = seg
            for dj in range(-k, k + 1):
                for di in range(-k, k + 1):
                    if (di or dj) and (di * di + dj * dj) * r.res ** 2 <= rad * rad and \
                            0 <= i + di < self.nx and 0 <= j + dj < self.ny:
                        idx = (j + dj) * self.nx + i + di
                        saved.append((idx, st[idx]))
                        st[idx] = -1
        return saved

    def unblock(self, saved):
        st = self.st_v[0]
        for idx, v in reversed(saved):
            st[idx] = v

    @staticmethod
    def segments(path):
        """('seg', layer, (i, j), (i, j)) straight runs and ('via', i, j) from a cell path"""
        out = []
        k = 0
        while k < len(path) - 1:
            l, i, j = path[k]
            l2, i2, j2 = path[k + 1]
            if l2 != l:
                out.append(('via', i, j))
                k += 1
                continue
            d = (i2 - i, j2 - j)
            m = k + 1
            while m + 1 < len(path) and path[m + 1][0] == l and (path[m + 1][1] - path[m][1], path[m + 1][2] - path[m][2]) == d:
                m += 1
            out.append(('seg', l, (i, j), (path[m][1], path[m][2])))
            k = m
        return out

    def conflict_cells(self, path, extra=(), nk=None, exn=()):
        """[(kind, l, i, j)] where a path meets another routed net (the net's own marks removed first): track cells,
        over the extra disk of a wide net away from its ends (nk cells: the neck, where the disk exn applies), and via
        cells (over exn)"""
        out = []
        nx, ny = self.nx, self.ny
        nk = int(self.r.neck / self.r.res) if nk is None else nk
        ends = (path[0], path[-1]) if path else ()
        for k, (l, i, j) in enumerate(path):
            dt = self.dy_t[l][0]
            ex = extra if extra and all((i - e[1]) ** 2 + (j - e[2]) ** 2 > nk * nk for e in ends) else exn
            if dt[j * nx + i] or any(0 <= i + di < nx and 0 <= j + dj < ny and dt[(j + dj) * nx + i + di]
                                     for di, dj in ex):
                out.append(('t', l, i, j))
            dv = self.dy_v[0]
            if k + 1 < len(path) and path[k + 1][0] != l and (
                    dv[j * nx + i] or any(0 <= i + di < nx and 0 <= j + dj < ny and dv[(j + dj) * nx + i + di]
                                          for di, dj in exn)):
                out.append(('v', l, i, j))
        return out

    def conflicts(self, path, extra=(), nk=None, exn=()):
        return len(self.conflict_cells(path, extra, nk, exn))


class Router:
    def __init__(self, grid, conns, log=print, pres0=0.5, pres_mul=1.5, hist_inc=1.0, via_cost=12.0, narrow=()):
        """narrow: nets routed at the default width and clearance (a wider class found no path for them)"""
        """conns: [(net name, a, z)], a / z = (x, y, layer name or None for any layer)"""
        self.g, self.log = grid, log
        self.conns = conns
        self.pres, self.pres_mul, self.hist_inc, self.via_cost = pres0, pres_mul, hist_inc, via_cost
        self.paths = {}                     # conn index -> path
        self.failed = set()
        b = grid.b
        self.code = {n: b.FindNet(n).GetNetCode() for n, _, _ in conns}
        self.narrow = set(narrow)
        # neck disk (default width near the ends, the net's own clearance) and via disk: the clearance above the
        # default class, rounded up to whole cells; a narrowed net has it all along
        self.extra_n = {n: self._disk(grid.cdef(n) - grid.r.c_def) for n, _, _ in conns}
        self.extra = {n: (self.extra_n[n] if n in self.narrow else max((self._extra(n, L) for L in grid.layers), key=len))
                      for n, _, _ in conns}
        kw = grid.r.keep_width or (lambda n: False)
        self.keep = {n for n, _, _ in conns if kw(n) and n not in self.narrow}
        self.nk = {n: (0 if n in self.keep else int(grid.r.neck / grid.r.res)) for n, _, _ in conns}

    def _disk(self, ext):
        r = self.g.r
        if ext <= 1e-6:
            return []
        k = int(math.ceil(ext / r.res))
        return [(di, dj) for dj in range(-k, k + 1) for di in range(-k, k + 1) if di * di + dj * dj <= k * k]

    def _extra(self, net, layer_name):
        """cells of the extra disk for nets wider (or with more clearance) than the default class"""
        g, r = self.g, self.g.r
        ext = (r.width_of(net, layer_name) / 2 + g.cdef(net)) - (r.h_def + r.c_def)
        if ext <= 1e-6:
            return []
        k = int(math.ceil(ext / r.res))              # rounded up to whole cells (an extra 0.025 mm is one cell)
        return [(di, dj) for dj in range(-k, k + 1) for di in range(-k, k + 1) if di * di + dj * dj <= k * k]

    def route_one(self, idx, margin):
        g, r = self.g, self.g.r
        net, a, z = self.conns[idx]
        code = self.code[net]
        ia, ja = g.ij(a[0], a[1])
        iz, jz = g.ij(z[0], z[1])
        m = int(margin / r.res)
        wi0, wj0 = max(0, min(ia, iz) - m), max(0, min(ja, jz) - m)
        wi1, wj1 = min(g.nx, max(ia, iz) + m + 1), min(g.ny, max(ja, jz) + m + 1)
        lc = (ctypes.c_double * g.nl)(*[(r.layer_cost or {}).get(L, 1.0 if L in ('F', 'B') else 1.15)
                                        for L in g.layers])
        la = -1 if a[2] is None else g.layers.index(a[2])
        lz = -1 if z[2] is None else g.layers.index(z[2])
        starts = (ctypes.c_int32 * 3)(la, ia, ja)
        goals = (ctypes.c_int32 * 3)(lz, iz, jz)
        ext = self.extra[net]
        ext_t = (ctypes.c_int32 * max(1, 2 * len(ext)))(*[v for p in ext for v in p])
        exn = self.extra_n[net]
        ext_v = (ctypes.c_int32 * max(1, 2 * len(exn)))(*[v for p in exn for v in p])
        cap = 200000
        out = (ctypes.c_int32 * (3 * cap))()
        P32, P16, PF = ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_float)
        st_t = (P32 * g.nl)(*[ctypes.cast(s[1], P32) for s in g.st_t])
        dy_t = (P16 * g.nl)(*[ctypes.cast(s[1], P16) for s in g.dy_t])
        hist = (PF * g.nl)(*[ctypes.cast(s[1], PF) for s in g.hist])
        n = lib().astar(g.nx, g.ny, g.nl, st_t, ctypes.cast(g.st_v[1], P32), dy_t, ctypes.cast(g.dy_v[1], P16),
                        hist, ctypes.cast(g.hist_v[1], PF), code, wi0, wj0, wi1 - wi0, wj1 - wj0, lc,
                        starts, 1, goals, 1, ext_t, len(ext), ext_v, len(exn), ext_v, len(exn),
                        self.via_cost, 0.3, 1.5, self.pres,
                        1, 20_000_000, self.nk[net] if ext else 0, r.full_states, out, cap)
        if n <= 0:
            return None
        return [(out[3 * k], out[3 * k + 1], out[3 * k + 2]) for k in range(n)]

    def run(self, iters=30):
        """negotiated congestion: each iteration rips up and re-routes every net (all its connections at once, so
        they do not see each other), then raises the history cost wherever a path meets another net's copper"""
        g = self.g
        nets = {}
        for k, (net, _, _) in enumerate(self.conns):
            nets.setdefault(net, []).append(k)
        order = sorted(nets, key=lambda n: -max(self._len(k) for k in nets[n]))
        bad = set(order)
        for it in range(iters):
            self.failed = set()
            # after the first pass only the nets in conflict are re-routed, with a full pass every fifth iteration
            todo = order if it % 5 == 0 else [n for n in order if n in bad]
            for net in todo:
                for k in nets[net]:
                    if k in self.paths:
                        g.mark(self.paths[k], net, -1)
                new = {}
                blocked = []                         # same-net vias of this net's earlier connections: hole spacing
                for k in nets[net]:
                    p = None
                    for margin in (6.0, 20.0):           # a wider window when the small one only offers conflicts
                        q = self.route_one(k, margin)
                        ex, nk, exn = self.extra[net], self.nk[net], self.extra_n[net]
                        if q and (p is None or g.conflicts(q, ex, nk, exn) < g.conflicts(p, ex, nk, exn)):
                            p = q
                        if p and not g.conflicts(p, ex, nk, exn):
                            break
                    if p:
                        new[k] = p
                        blocked += g.block_vias_near(p)
                    else:
                        self.failed.add(k)
                        self.paths.pop(k, None)
                g.unblock(blocked)
                for k, p in new.items():
                    self.paths[k] = p
                for k in nets[net]:
                    if k in self.paths:
                        g.mark(self.paths[k], net, +1)
            over, bad = 0, set()
            for net in order:
                ks = [k for k in nets[net] if k in self.paths]
                for k in ks:
                    g.mark(self.paths[k], net, -1)
                ex = self.extra[net]
                for k in ks:
                    for kind, l, i, j in g.conflict_cells(self.paths[k], ex, self.nk[net], self.extra_n[net]):
                        c = j * g.nx + i
                        if kind == 't':
                            g.hist[l][0][c] += self.hist_inc
                        else:
                            g.hist_v[0][c] += self.hist_inc
                        over += 1
                        bad.add(net)
                for k in ks:
                    g.mark(self.paths[k], net, +1)
            self.log(f'  iteration {it + 1}: {len(todo)} nets re-routed, {len(self.paths)} connections routed, '
                     f'{len(self.failed)} unroutable, {len(bad)} nets in conflict ({over} cells), '
                     f'present factor {self.pres:.2f}')
            bad |= {self.conns[k][0] for k in self.failed}
            if over == 0 and not self.failed:
                return True
            self.pres = min(300.0, self.pres * self.pres_mul)    # float32 path costs: keep unit steps visible
            order = [n for n in order if n in bad] + [n for n in order if n not in bad]
        return False

    def hotspots(self, committed):
        """(x, y) of the cells where the paths left out of the commit meet other nets' copper"""
        g = self.g
        out = []
        for k, p in self.paths.items():
            if k in committed:
                continue
            net = self.conns[k][0]
            ks = [q for q in self.paths if self.conns[q][0] == net]
            for q in ks:
                g.mark(self.paths[q], net, -1)
            out += [g.xy(i, j) for _, l, i, j in g.conflict_cells(p, self.extra[net], self.nk[net],
                                                                  self.extra_n[net])]
            for q in ks:
                g.mark(self.paths[q], net, +1)
        return out

    def _len(self, k):
        _, a, z = self.conns[k]
        return math.dist(a[:2], z[:2])

    def commit(self, conflicts_ok=False):
        """tracks and vias onto the board (conflicting paths are left out unless conflicts_ok); returns the indices of
        the connections committed"""
        g, r = self.g, self.g.r
        added = set()
        by_net = {}
        for k in self.paths:
            by_net.setdefault(self.conns[k][0], []).append(k)
        bad = set()
        for net, ks in by_net.items():
            for k in ks:
                g.mark(self.paths[k], net, -1)
            bad |= {k for k in ks if g.conflicts(self.paths[k], self.extra[net], self.nk[net], self.extra_n[net])}
            for k in ks:
                g.mark(self.paths[k], net, +1)
        for k, p in self.paths.items():
            net, a, z = self.conns[k]
            if k in bad and not conflicts_ok:
                continue
            segs = Grid.segments(p)
            # the path runs on cell centres; the item it starts / ends on (a pad, a track end, a via) may sit up to half
            # a cell off: a short stub joins them, within the item's own copper (default width; an impedance net's
            # own width)
            for e, (l, i, j) in ((a, p[0]), (z, p[-1])):
                c = g.xy(i, j)
                if math.dist(c, e[:2]) > 1e-4:
                    sw = r.width_of(net, g.layers[l]) if net in self.keep else 2 * r.h_def
                    R.add_track(g.b, net, g.layers[l], [e[:2], c], sw, locked=False)
            for s_i, s in enumerate(segs):
                if s[0] == 'via':                  # the router's copper stays unlocked: gndfix.rip_up_near may move it
                    x, y = g.xy(s[1], s[2])
                    R.add_via(g.b, net, x, y, *r.via, locked=False)
                    continue
                _, li, c0, c1 = s
                p0, p1 = g.xy(*c0), g.xy(*c1)
                w = 2 * r.h_def if net in self.narrow else r.width_of(net, g.layers[li])
                if net not in self.keep and (w > 2 * r.h_def + 1e-6 or g.cdef(net) > r.c_def + 1e-6):
                    # wide net: default width at the ends
                    for piece, pw in _neck_pieces([p0, p1], [a[:2], z[:2]], r.neck + w / 2 + 0.03, w, 2 * r.h_def):
                        R.add_track(g.b, net, g.layers[li], piece, pw, locked=False)
                else:
                    R.add_track(g.b, net, g.layers[li], [p0, p1], w, locked=False)
            added.add(k)
        return added


def _neck_pieces(p, ends, rad, width, narrow):
    """split a polyline at the circles of radius rad around the ends: narrow inside, full width outside"""
    def wid(q):
        return narrow if any(math.dist(q, e) <= rad for e in ends) else width
    pts = [p[0]]
    for u, v in zip(p, p[1:]):
        n = max(1, int(math.dist(u, v) / 0.025))
        pts += [(u[0] + (v[0] - u[0]) * i / n, u[1] + (v[1] - u[1]) * i / n) for i in range(1, n + 1)]
    out, cur, cw = [], [pts[0]], wid(pts[0])
    for q in pts[1:]:
        w = wid(q)
        if w < cw:                                   # into a narrow zone: the boundary segment is narrow
            out.append((cur, cw))
            cur, cw = [cur[-1], q], w
            continue
        cur.append(q)
        if w != cw:                                  # out of it: the narrow piece ends at the first wide point
            out.append((cur, cw))
            cur, cw = [q], w
    out.append((cur, cw))
    return [([c[0], c[-1]], w) for c, w in out if math.dist(c[0], c[-1]) > 1e-4]


# ------------------------------------------------------------------------------------- open connections (KiCad)
def drc(path, refill=True):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'drc.json')
        cmd = ['kicad-cli', 'pcb', 'drc', '--format', 'json', '-o', out]
        if refill:
            cmd.append('--refill-zones')
        subprocess.run(cmd + [path], check=True, capture_output=True)
        return json.load(open(out))


def open_connections(b, path, layers, skip_nets=('GND',), no_zone_ends=('GND',), log=print):
    """[(net, a, z)] for KiCad's unconnected items (zones refilled), endpoints on the items themselves. For the nets
    in no_zone_ends KiCad names the whole pour, not the cut-off piece: a pad / track to a zone is aimed at the nearest
    via of its net. A zone to a zone (any net: a pour cut in two by other nets' vias) is worked out from the fill
    (zone_split)"""
    d = drc(path)
    by = {}
    for fp in R.footprints(b):
        for p in R.pads(fp):
            by[p.m_Uuid.AsString()] = p
    for t in R.tracks(b):
        by[t.m_Uuid.AsString()] = t
    for z in b.Zones():
        by[z.m_Uuid.AsString()] = z
    conns, skipped, split = [], [], {}
    for u in d['unconnected_items']:
        its = [by.get(i['uuid']) for i in u['items']]
        pos = [(i['pos']['x'] - R.O, i['pos']['y'] - R.O) for i in u['items']]
        if any(i is None for i in its):
            skipped.append(u)
            continue
        net = its[0].GetNetname()
        if net.split('/')[-1] in skip_nets:
            continue
        if all(isinstance(i, pcbnew.ZONE) for i in its):
            split.setdefault(net, []).append(u)     # zone to zone: the pieces are found from the fill (zone_split)
            continue
        if net.split('/')[-1] in no_zone_ends and any(isinstance(i, pcbnew.ZONE) for i in its):
            # KiCad names the whole pour: a pad / track on the other side is aimed at the nearest via of its net
            other = [(i, p) for i, p in zip(its, pos) if not isinstance(i, pcbnew.ZONE)]
            v = _nearest_via(b, its[0].GetNetCode(), other[0][1]) if other else None
            if v is None:
                skipped.append(u)
                continue
            a = _end(other[0][0], v, layers)
            if a is None:
                skipped.append(u)
                continue
            conns.append((net, a, (v[0], v[1], None)))
            continue
        ends = [_end(its[0], pos[1], layers), _end(its[1], pos[0], layers)]
        if None in ends:
            skipped.append(u)
            continue
        ends.sort(key=lambda e: (round(e[0], 4), round(e[1], 4)))       # (the report's item order varies)
        conns.append((net, ends[0], ends[1]))
    for net in sorted(split):
        cs = zone_split(b, net, layers)
        if cs:
            conns += cs
        else:
            skipped += split[net]
    # the DRC report stops listing unconnected items at an error limit (499 in KiCad 10): when it is that long, every
    # net's open connections come from pcbnew's connectivity instead (nets listed in part included)
    if len(d['unconnected_items']) >= DRC_LIST_CAP:
        listed = {}
        for u in d['unconnected_items']:
            it = by.get(u['items'][0]['uuid'])
            if it is not None:
                listed[it.GetNetname()] = listed.get(it.GetNetname(), 0) + 1
        more, n_extra = ratsnest(b, layers, skip_nets)
        for net, cs in more.items():
            if len(cs) > listed.get(net, 0):
                conns = [c for c in conns if c[0] != net] + cs
                n_extra += len(cs) - listed.get(net, 0)
        log(f'DRC list capped at {len(d["unconnected_items"])}: {n_extra} more open connections from the connectivity')
    # KiCad lists them in a run-dependent order; the negotiation depends on the order, so make it reproducible
    conns.sort(key=lambda c: (c[0], round(c[1][0], 3), round(c[1][1], 3), round(c[2][0], 3), round(c[2][1], 3)))
    log(f'{len(d["unconnected_items"])} open connections in KiCad, {len(conns)} to route, {len(skipped)} skipped')
    return conns, skipped


DRC_LIST_CAP = 499


def ratsnest(b, layers, skip_nets=()):
    """open connections from pcbnew's connectivity (zones filled here): per net, the clusters of connected items,
    joined by a minimum spanning tree over their nearest anchors (pads, vias, track ends; a cluster of zones only has
    none and is left out). Returns ({net: [(net, a, z)]}, 0)"""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    c = b.GetConnectivity()
    items = {}
    for fp in R.footprints(b):
        for p in R.pads(fp):
            if p.GetNetCode() > 0:
                items.setdefault(p.GetNetCode(), []).append(p)
    for t in R.tracks(b):
        if t.GetNetCode() > 0:
            items.setdefault(t.GetNetCode(), []).append(t)
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetCode() > 0:
            items.setdefault(z.GetNetCode(), []).append(z)
    out = {}
    for code, its in items.items():
        net = its[0].GetNetname()
        if net.split('/')[-1] in skip_nets or len(its) < 2:
            continue
        uid = {it.m_Uuid.AsString(): it for it in its}
        parent = {u: u for u in uid}

        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u
        for u, it in uid.items():
            for q in c.GetConnectedItems(it):
                v = q.m_Uuid.AsString()
                if v in uid:
                    parent[find(v)] = find(u)
        groups = {}
        for u, it in uid.items():
            groups.setdefault(find(u), []).append(it)
        if len(groups) < 2:
            continue
        anchors = [a for a in (_anchors(g) for g in groups.values()) if a]
        if len(anchors) < 2:
            continue
        out[net] = _join(net, anchors, layers)
    return out, 0


def _anchors(group):
    a = []
    for it in group:
        if isinstance(it, pcbnew.PAD) or isinstance(it, pcbnew.PCB_VIA):
            a.append((R.to_mm(it.GetPosition()), it))
        elif isinstance(it, pcbnew.PCB_TRACK):
            a += [(R.to_mm(it.GetStart()), it), (R.to_mm(it.GetEnd()), it)]
    return a


def _join(net, anchors, layers):
    """[(net, a, z)] joining clusters (lists of (point, item) anchors) by a minimum spanning tree over their nearest
    anchors (Prim, the biggest cluster first)"""
    anchors = sorted(anchors, key=len, reverse=True)
    best = {k: None for k in range(1, len(anchors))}    # k: (distance, anchor in the tree, anchor of cluster k)

    def relax(new):
        for k in best:
            for p, ip in anchors[new]:
                for q, iq in anchors[k]:
                    d = math.dist(p, q)
                    if best[k] is None or d < best[k][0]:
                        best[k] = (d, (p, ip), (q, iq))
    relax(0)
    cs = []
    while best:
        k = min(best, key=lambda k: best[k][0])
        _, (p, ip), (q, iq) = best.pop(k)
        a, z = _end(ip, q, layers), _end(iq, p, layers)
        if a is not None and z is not None:
            a, z = sorted((a, z), key=lambda e: (round(e[0], 4), round(e[1], 4)))
            cs.append((net, a, z))
        relax(k)
    return cs


def zone_split(b, net, layers):
    """open connections of a net whose copper falls apart only between pieces of its pours (KiCad then names two
    whole zones): the net's pads, tracks and vias are clustered with every fill polygon as a node of its own (an item
    joins a polygon its copper touches), and the clusters are joined as in ratsnest"""
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.BuildConnectivity()
    c = b.GetConnectivity()
    code = b.FindNet(net).GetNetCode()
    its = [p for fp in R.footprints(b) for p in R.pads(fp) if p.GetNetCode() == code]
    its += [t for t in R.tracks(b) if t.GetNetCode() == code]
    uid = {it.m_Uuid.AsString(): it for it in its}
    parent = {}

    def find(u):
        parent.setdefault(u, u)
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u
    for u, it in uid.items():
        find(u)
        for q in c.GetConnectedItems(it):
            v = q.m_Uuid.AsString()
            if v in uid and not isinstance(q, pcbnew.ZONE):
                parent[find(v)] = find(u)
    touch = pcbnew.FromMM(0.005)
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != code:
            continue
        for L in z.GetLayerSet().CuStack():
            fill = z.GetFilledPolysList(L)
            for i in range(fill.OutlineCount()):
                sp = pcbnew.SHAPE_POLY_SET()
                sp.AddOutline(fill.Outline(i))
                for h in range(fill.HoleCount(i)):
                    sp.AddHole(fill.Hole(i, h))
                key = f'{z.m_Uuid.AsString()}/{L}/{i}'
                find(key)
                box = sp.BBox()
                for u, it in uid.items():
                    if (it.IsOnLayer(L) and box.Intersects(it.GetBoundingBox())
                            and sp.Collide(it.GetEffectiveShape(L), touch)):
                        parent[find(u)] = find(key)
    groups = {}
    for u, it in uid.items():
        groups.setdefault(find(u), []).append(it)
    anchors = [a for a in (_anchors(g) for g in groups.values()) if a]
    return _join(net, anchors, layers) if len(anchors) > 1 else []


def _nearest_via(b, code, p, rmin=0.6, rmax=5.0):
    """the nearest via of net `code` between rmin and rmax mm from p (not one sitting on the item itself)"""
    best = None
    for t in R.tracks(b):
        if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == code:
            q = R.to_mm(t.GetPosition())
            d = math.dist(q, p)
            if rmin <= d <= rmax and (best is None or d < best[0]):
                best = (d, q)
    return best[1] if best else None


def _end(item, toward, layers):
    if isinstance(item, pcbnew.PAD):
        x, y = R.to_mm(item.GetPosition())
        if item.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            return x, y, None
        return x, y, 'B' if item.IsOnLayer(pcbnew.B_Cu) else 'F'
    if isinstance(item, pcbnew.PCB_VIA):
        x, y = R.to_mm(item.GetPosition())
        return x, y, None
    if isinstance(item, pcbnew.PCB_TRACK):
        L = {v: k for k, v in R.LAYER.items()}.get(item.GetLayer())
        if L not in layers:
            return None
        a, z = R.to_mm(item.GetStart()), R.to_mm(item.GetEnd())
        p = min((a, z), key=lambda q: math.dist(q, toward))
        # a track end on a via of its net is the via (any layer): KiCad's report names either one, depending on
        # the items' random UUIDs, and the route must not depend on that
        code = item.GetNetCode()
        if any(isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == code and math.dist(R.to_mm(t.GetPosition()), p) < 1e-3
               for t in R.tracks(item.GetBoard())):
            return p[0], p[1], None
        return p[0], p[1], L
    if isinstance(item, pcbnew.ZONE):
        # outline points nearest to the other item, pulled 0.4-1.3 mm toward the zone's inside, at the first one with
        # no other net's pad or via within 0.6 mm (the pour is filled around those: a point there is not copper)
        cands = []
        for L in layers:
            if not item.IsOnLayer(R.LAYER[L]):
                continue
            o = item.Outline()
            for k in range(o.OutlineCount()):
                ch = o.Outline(k)
                n = ch.PointCount()
                for i in range(n):
                    p, q = R.to_mm(ch.CPoint(i)), R.to_mm(ch.CPoint((i + 1) % n))
                    for t in (0.25, 0.5, 0.75):
                        e = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                        cands.append((math.dist(e, toward), e, L))
        if not cands:
            return None
        cands.sort(key=lambda c: c[0])
        b = item.GetBoard()
        code = item.GetNetCode()
        others = [R.to_mm(t.GetPosition()) for t in R.tracks(b) if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() != code]
        others += [R.to_mm(p.GetPosition()) for fp in R.footprints(b) for p in R.pads(fp) if p.GetNetCode() != code]
        o = item.Outline()
        for _, e, L in cands[:12]:
            near = [q for q in others if math.dist(q, e) < 2.5]
            for step in (0.4, 0.6, 0.9, 1.3):
                for ang in range(0, 360, 30):
                    x, y = e[0] + step * math.cos(math.radians(ang)), e[1] + step * math.sin(math.radians(ang))
                    if o.Contains(pcbnew.VECTOR2I(R.nm(R.O + x), R.nm(R.O + y))) and \
                            all(math.dist((x, y), q) >= 0.6 for q in near):
                        return x, y, L
        return None
    return None


def merge_close_vias(b, drill, hole_to_hole, log=print):
    """same-net vias on the same spot (two connections of one net may share a cell): the router's via goes, its
    tracks stay on the via that is kept (a locked one if any). Closer-than-hole-spacing pairs cannot arise: the
    router keeps a net's vias apart (Grid.block_vias_near)"""
    dmin = 1e-3                                        # exact duplicates only: moving copper is not safe
    vias = {}
    for t in R.tracks(b):
        if isinstance(t, pcbnew.PCB_VIA):
            vias.setdefault(t.GetNetCode(), []).append(t)
    ends = {}
    for t in R.tracks(b):
        if not isinstance(t, pcbnew.PCB_VIA):
            ends.setdefault(t.GetNetCode(), []).append(t)
    gone = 0
    for code, vs in vias.items():
        vs.sort(key=lambda v: not v.IsLocked())                  # locked ones are kept first
        kept = []
        for v in vs:
            p = R.to_mm(v.GetPosition())
            k = next((q for q in kept if math.dist(R.to_mm(q.GetPosition()), p) < dmin), None)
            if k is None or v.IsLocked():
                kept.append(v)
                continue
            target = k.GetPosition()
            for t in ends.get(code, ()):
                if t.GetStart() == v.GetPosition():
                    t.SetStart(target)
                if t.GetEnd() == v.GetPosition():
                    t.SetEnd(target)
            R.remove(b, v)
            gone += 1
    if gone:
        log(f'{gone} duplicate router vias removed')
    return gone


def log_drc(path, log=print):
    """KiCad's DRC of the saved board, summarised: errors and warnings by type, open connections"""
    import collections
    d = drc(path, refill=False)
    c = collections.Counter((v['severity'], v['type']) for v in d['violations'])
    log('DRC: ' + ', '.join(f'{n} {sev} {t}' for (sev, t), n in sorted(c.items())) +
        f'; {len(d["unconnected_items"])} unconnected')
    return d
