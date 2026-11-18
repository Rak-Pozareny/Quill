"""Grid router for the pre-routed nets of Board A: differential pairs (coupled) and short single traces.

Freerouting routes everything else afterwards; it cannot route coupled pairs. This router works on a square grid
over a window of the board:

- Obstacles are rasterised from the board's own copper (pads, tracks, vias, zones, holes, board edge), each shape
  inflated by KiCad (TransformShapeToPolygon) by the clearance plus the half-width of what is being routed, so a free
  grid cell is a legal centreline position.
- A differential pair is routed as one fat centreline (half-width W + S/2) and then offset into its two traces.
  Layer changes use a via pair; the via grid is inflated on every routing layer.
- Search is A* over (x, y, layer, direction) with 45 degree steps only (no 90 degree corners), a via cost and
  per-layer costs.

Coordinates: board mm (origin top-left of the board; the file has it at +100/+100).
"""
import heapq
import math

import pcbnew

O = 100.0
LAYER = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'In3': pcbnew.In3_Cu, 'B': pcbnew.B_Cu}
ROUTE_LAYERS = ('F', 'In2', 'In3', 'B')
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]     # 0 = +x, 2 = +y (y down)
MAXERR = pcbnew.FromMM(0.005)


def tracks(board):
    """board tracks and vias (the SWIG iterator is broken under Python 3.14; index access works)"""
    ts = board.Tracks()
    out = []
    for i in range(len(ts)):
        t = ts[i]
        out.append(t.Cast() if hasattr(t, 'Cast') else t)
    return out


def strip_routing_file(path, heads=('segment', 'via', 'arc', 'zone')):
    """remove the board-level tracks, vias and zones from a .kicad_pcb file (text level: removing thousands of items
    through the Python bindings leaves them unstable). Returns the number of items removed"""
    t = open(path).read()
    out, i, n, depth = [], 0, 0, 0
    k = 0
    while k < len(t):
        c = t[k]
        if c == '(':
            if depth == 1:
                j = k + 1
                while t[j].isalnum() or t[j] == '_':
                    j += 1
                if t[k + 1:j] in heads:                     # skip this whole top-level item
                    d, m = 0, k
                    while True:
                        d += {'(': 1, ')': -1}.get(t[m], 0)
                        m += 1
                        if d == 0:
                            break
                    while m < len(t) and t[m] in ' \t':
                        m += 1
                    if m < len(t) and t[m] == '\n':
                        m += 1
                    out.append(t[i:k].rstrip(' \t'))
                    i = k = m
                    n += 1
                    continue
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == '"':                                      # skip strings (may hold parentheses)
            k += 1
            while t[k] != '"':
                k += 2 if t[k] == '\\' else 1
        k += 1
    out.append(t[i:])
    if n:
        open(path, 'w').write(''.join(out))
    return n


def footprints(board):
    """the board's footprints by index (iterating GetFootprints() can hand back raw SWIG objects under Python 3.14
    once items have been removed)"""
    fps = board.Footprints()
    return [fps[i] for i in range(len(fps))]


def remove(board, item):
    """board.Remove(item), the item left unowned: Remove() hands it to Python, SWIG finds no destructor when its wrapper
    is collected, and after a few hundred of those the bindings hand back raw SwigPyObjects (footprints without
    Pads()). The removed item leaks instead, a few hundred bytes"""
    board.Remove(item)
    item.thisown = False


def net_names(board):
    """names of the nets that have pads (GetNetsByName() has the same SWIG problem as GetFootprints())"""
    return sorted({p.GetNetname() for fp in footprints(board) for p in pads(fp) if p.GetNetname()})


def pads(fp):
    pp = fp.Pads()
    return [pp[i] for i in range(len(pp))]


def nm(v):
    return pcbnew.FromMM(v)


def to_mm(p):
    return pcbnew.ToMM(p.x) - O, pcbnew.ToMM(p.y) - O


class Window:
    def __init__(self, x0, y0, x1, y1, res):
        self.res = res
        self.x0, self.y0 = x0, y0
        self.nx = int(math.ceil((x1 - x0) / res)) + 1
        self.ny = int(math.ceil((y1 - y0) / res)) + 1

    def ij(self, x, y):
        return int(round((x - self.x0) / self.res)), int(round((y - self.y0) / self.res))

    def xy(self, i, j):
        return self.x0 + i * self.res, self.y0 + j * self.res

    def inside(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny

    def grid(self):
        return bytearray(self.nx * self.ny)


def fill_poly(win, g, pts, val=1):
    """scanline fill of one closed polygon (list of (x, y) mm) into grid g, sampling cell centres"""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    j0 = max(0, int(math.ceil((min(ys) - win.y0) / win.res)))
    j1 = min(win.ny - 1, int(math.floor((max(ys) - win.y0) / win.res)))
    n = len(pts)
    edges = [(pts[k], pts[(k + 1) % n]) for k in range(n) if pts[k][1] != pts[(k + 1) % n][1]]
    for j in range(j0, j1 + 1):
        y = win.y0 + j * win.res
        xs = []
        for (ax, ay), (bx, by) in edges:
            if (ay <= y < by) or (by <= y < ay):
                xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
        xs.sort()
        row = j * win.nx
        for k in range(0, len(xs) - 1, 2):
            i0 = max(0, int(math.ceil((xs[k] - win.x0) / win.res)))
            i1 = min(win.nx - 1, int(math.floor((xs[k + 1] - win.x0) / win.res)))
            if i1 >= i0:
                g[row + i0:row + i1 + 1] = bytes([val]) * (i1 - i0 + 1)


def fill_polyset(win, g, ps, val=1):
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k)
        fill_poly(win, g, [to_mm(o.CPoint(i)) for i in range(o.PointCount())], val)


def _bbox_hit(win, bb, margin):
    x0, y0 = to_mm(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
    x1, y1 = to_mm(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
    return not (x1 + margin < win.x0 or x0 - margin > win.x0 + win.nx * win.res or
                y1 + margin < win.y0 or y0 - margin > win.y0 + win.ny * win.res)


def hole_poly(it, inflate):
    """drill hole of a pad or via, inflated, as a SHAPE_POLY_SET"""
    hs = pcbnew.SHAPE_POLY_SET()
    if isinstance(it, pcbnew.PAD):
        it.TransformHoleToPolygon(hs, nm(inflate), MAXERR, pcbnew.ERROR_OUTSIDE)
        return hs
    c = it.GetPosition()
    r = it.GetDrillValue() / 2 + nm(inflate)
    hs.NewOutline()
    for k in range(24):
        a = 2 * math.pi * k / 24
        hs.Append(int(c.x + r / math.cos(math.pi / 24) * math.cos(a)), int(c.y + r / math.cos(math.pi / 24) * math.sin(a)))
    return hs


_ESC = {}
ESCAPE_LAND = 0.2      # radius of the via landing reserved at the end of each escape stub (the board's via / 2)


def escape_corridors(board):
    """virtual escape stubs of the signal pins of fine-pitch parts (pad pitch <= 0.65 mm, >= 6 SMD pads): each
    non-GND pad gets a 0.1 mm-wide stub 0.6 mm out along its long axis, away from the part's pads' centre, ending in
    a via landing of radius ESCAPE_LAND. [(net code, layer name, pitch, polygon pts, is landing)], cached per board"""
    key = (id(board), ESCAPE_LAND)
    if key in _ESC:
        return _ESC[key]
    out = []
    for fp in footprints(board):
        smd = [p for p in pads(fp) if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetNumber()]
        if len(smd) < 6:
            continue
        cs = [to_mm(p.GetPosition()) for p in smd]
        pitch = min(math.dist(a, b) for i, a in enumerate(cs) for b in cs[i + 1:])
        if pitch > 0.66 or pitch < 0.2:
            continue
        cx, cy = sum(c[0] for c in cs) / len(cs), sum(c[1] for c in cs) / len(cs)
        for p, c in zip(smd, cs):
            if p.GetNetCode() <= 0 or p.GetNetname().split('/')[-1] == 'GND':
                continue
            bb = p.GetBoundingBox()
            w, h = nm_to_mm(bb.GetWidth()), nm_to_mm(bb.GetHeight())
            if abs(w - h) < 0.05:
                continue
            ax = (1.0, 0.0) if w > h else (0.0, 1.0)
            sg = 1 if (c[0] - cx) * ax[0] + (c[1] - cy) * ax[1] >= 0 else -1
            ext = max(w, h) / 2
            a = (c[0] + ax[0] * sg * ext, c[1] + ax[1] * sg * ext)
            z = (c[0] + ax[0] * sg * (ext + 0.6), c[1] + ax[1] * sg * (ext + 0.6))
            hw = 0.05
            nx, ny = -ax[1], ax[0]
            pts = [(a[0] + nx * hw, a[1] + ny * hw), (z[0] + nx * hw, z[1] + ny * hw),
                   (z[0] - nx * hw, z[1] - ny * hw), (a[0] - nx * hw, a[1] - ny * hw)]
            L = 'B' if p.IsOnLayer(pcbnew.B_Cu) else 'F'
            out.append((p.GetNetCode(), L, pitch, pts, False))
            land = [(z[0] + ESCAPE_LAND * math.cos(k * math.pi / 8), z[1] + ESCAPE_LAND * math.sin(k * math.pi / 8))
                    for k in range(16)]
            out.append((p.GetNetCode(), L, pitch, land, True))
    _ESC[key] = out
    return out


def nm_to_mm(v):
    return pcbnew.ToMM(v)


class Obstacles:
    """rasterised obstacles of one board for one route: per routing layer, plus a via grid"""

    def __init__(self, board, win, own_nets, half, clearance, via_r=None, hole_clr=0.2, edge_clr=0.2, layers=ROUTE_LAYERS,
                 extra_keepouts=(), net_clr=None, zones=True, escapes=None, solid=()):
        """half: half-width of the routed copper, a number or {layer: number}; net_clr: {net code: clearance} for
        nets that may come closer (the other trace of a differential pair); zones=False: copper pours of other nets
        are not obstacles (they are filled afterwards and flow around what is added), rule-area keepouts still are;
        zones='hull': of the pours only the small switch-node / loop ones are obstacles;
        solid: tracks / vias of the own nets that are obstacles all the same (a pair's own fan-out vias under its
        coupled section). Holes of any net, the own ones included, keep vias at the hole-to-hole distance"""
        net_clr = net_clr or {}
        solid = {t.m_Uuid.AsString() for t in solid}
        if not isinstance(half, dict):
            half = {L: half for L in layers}
        hmax = max(half.values())
        self.win, self.layers = win, layers
        self.g = {L: win.grid() for L in layers}
        self.v = win.grid() if via_r else None
        own = set(own_nets)
        items = []
        for fp in footprints(board):
            for p in pads(fp):
                items.append(p)
            for z in fp.Zones():
                items.append(z)
            g = fp.GraphicalItems()                  # copper shapes in footprints (net ties)
            for k in range(len(g)):
                it = g[k].Cast()
                if isinstance(it, pcbnew.PCB_SHAPE) and it.IsOnCopperLayer():
                    items.append(it)
        items += tracks(board)
        items += list(board.Zones())
        for it in items:
            if not _bbox_hit(win, it.GetBoundingBox(), hmax + clearance + 1.0):
                continue
            net = it.GetNetCode() if hasattr(it, 'GetNetCode') else 0
            is_zone = isinstance(it, pcbnew.ZONE)
            own_it = net in own and net != 0 and not (solid and it.m_Uuid.AsString() in solid)
            if is_zone and it.GetIsRuleArea():
                if not it.GetDoNotAllowTracks():
                    continue
                for L in layers:
                    if it.IsOnLayer(LAYER[L]):
                        ps = it.Outline().CloneDropTriangulation()
                        ps.Inflate(nm(half[L]), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                        fill_polyset(win, self.g[L], ps)
                if self.v is not None and it.GetDoNotAllowVias():
                    ps = it.Outline().CloneDropTriangulation()
                    ps.Inflate(nm(via_r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                    fill_polyset(win, self.v, ps)
                continue
            if is_zone and (net in own or not zones or
                            (zones == 'hull' and not it.GetZoneName().endswith('(hull)'))):
                continue
            if is_zone and it.GetLayer() in (pcbnew.In1_Cu, pcbnew.In4_Cu):
                continue                      # GND planes: vias clear them, nothing is routed on them
            clr = net_clr.get(net, clearance)
            for L in layers:
                lid = LAYER[L]
                if not it.IsOnLayer(lid):
                    continue
                if own_it:
                    continue
                ps = pcbnew.SHAPE_POLY_SET()
                if is_zone:
                    ps = it.Outline().CloneDropTriangulation()
                    ps.Inflate(nm(half[L] + clr), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                else:
                    it.TransformShapeToPolygon(ps, lid, nm(half[L] + clr), MAXERR, pcbnew.ERROR_OUTSIDE)
                fill_polyset(win, self.g[L], ps)
            # vias of the route must clear every copper item on every routing layer, and every hole; a pour named
            # '... (vias pass)' is filled after routing and flows around the vias of other nets, so it only blocks tracks
            via_pass = is_zone and it.GetZoneName().endswith('(vias pass)')
            if self.v is not None and not own_it and not via_pass:
                for L in layers:
                    lid = LAYER[L]
                    if it.IsOnLayer(lid):
                        ps = pcbnew.SHAPE_POLY_SET()
                        if is_zone:
                            ps = it.Outline().CloneDropTriangulation()
                            ps.Inflate(nm(via_r + clearance), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                        else:
                            # a via hole keeps 0.3 mm from plated-through pad copper (the PTH rule applies both ways)
                            pthp = isinstance(it, pcbnew.PAD) and it.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                            vc = via_r + (max(clearance, 0.2) if pthp else clearance)
                            it.TransformShapeToPolygon(ps, lid, nm(vc), MAXERR, pcbnew.ERROR_OUTSIDE)
                        fill_polyset(win, self.v, ps)
            # holes: drill clearance to the copper of other nets on every layer (JLC: via hole and NPTH 0.2, PTH 0.28,
            # 0.3 on inner layers), and hole to hole for vias of every net, the own ones too (0.2 mm + the 0.1 mm via
            # drill radius below the via copper radius, + 0.02 grid margin)
            if isinstance(it, (pcbnew.PAD, pcbnew.PCB_VIA)) and it.HasHole():
                pth = isinstance(it, pcbnew.PAD) and it.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                hc = max(hole_clr, 0.3) if pth else hole_clr
                if not own_it:
                    for L in layers:
                        fill_polyset(win, self.g[L], hole_poly(it, half[L] + hc))
                if self.v is not None:
                    fill_polyset(win, self.v, hole_poly(it, via_r + (0.12 if own_it else max(0.25, hc + 0.02))))
        # other nets' escape stubs (see escape_corridors): 'all' fine-pitch parts with their via landings, or 'coarse'
        # (the stubs of the parts with pitch >= 0.45 mm, no landings: for the pair router)
        if escapes:
            for code, L, pitch, pts, landing in escape_corridors(board):
                if code in own or L not in layers or (escapes == 'coarse' and (pitch < 0.45 or landing)):
                    continue
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                if max(xs) < win.x0 - 1 or min(xs) > win.x0 + win.nx * win.res + 1 or \
                        max(ys) < win.y0 - 1 or min(ys) > win.y0 + win.ny * win.res + 1:
                    continue
                ps = pcbnew.SHAPE_POLY_SET()
                ps.NewOutline()
                for x, y in pts:
                    ps.Append(nm(O + x), nm(O + y))
                t = ps.CloneDropTriangulation()
                t.Inflate(nm(half[L] + clearance), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                fill_polyset(win, self.g[L], t)
                if self.v is not None:
                    t = ps.CloneDropTriangulation()
                    t.Inflate(nm(via_r + clearance), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
                    fill_polyset(win, self.v, t)
        for k in extra_keepouts:            # (layer, '*' or 'via', polygon pts) in mm
            L, pts = k
            if L == 'via':
                if self.v is not None:
                    fill_poly(win, self.v, pts)
                continue
            for LL in (layers if L == '*' else [L]):
                if LL in self.g:
                    fill_poly(win, self.g[LL], pts)
        # board edge: free only inside the outline shrunk by edge clearance + half-width
        outl = pcbnew.SHAPE_POLY_SET()
        board.GetBoardPolygonOutlines(outl, False)
        for L, r in [(L, half[L] + edge_clr) for L in layers] + ([('via', via_r + edge_clr)] if self.v is not None else []):
            inside = win.grid()
            o2 = outl.CloneDropTriangulation()
            o2.Deflate(nm(r), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, MAXERR)
            for k in range(o2.OutlineCount()):
                fill_poly(win, inside, [to_mm(o2.Outline(k).CPoint(i)) for i in range(o2.Outline(k).PointCount())])
                for h in range(o2.HoleCount(k)):
                    hh = o2.Hole(k, h)
                    fill_poly(win, inside, [to_mm(hh.CPoint(i)) for i in range(hh.PointCount())], 0)
            tgt = self.v if L == 'via' else self.g[L]
            for c in range(len(tgt)):
                if not inside[c]:
                    tgt[c] = 1

    def free(self, L, i, j):
        w = self.win
        return 0 <= i < w.nx and 0 <= j < w.ny and not self.g[L][j * w.nx + i]

    def via_free(self, i, j):
        w = self.win
        return self.v is not None and 0 <= i < w.nx and 0 <= j < w.ny and not self.v[j * w.nx + i]

    def clear_disk(self, L, x, y, r):
        """open a small disk (route start / end at a pad) on layer L, or on the via grid if L == 'via'"""
        w = self.win
        g = self.v if L == 'via' else self.g[L]
        ci, cj = w.ij(x, y)
        k = int(math.ceil(r / w.res))
        for j in range(cj - k, cj + k + 1):
            for i in range(ci - k, ci + k + 1):
                if w.inside(i, j) and (i - ci) ** 2 + (j - cj) ** 2 <= k * k:
                    g[j * w.nx + i] = 0


def astar(obs, starts, goals, layer_cost, via_cost, turn_cost=0.4, allow_vias=True, max_expand=4_000_000,
          via_straight=0, no_via=()):
    """starts / goals: lists of (x, y, L, dir or None). Returns [(x, y, L)] centreline cells or None.
    dir None = any direction. A goal is reached on its cell and layer, arriving in its direction (if given).
    via_straight > 0: a layer change is via_straight cells straight on, the via, via_straight cells straight on (a pair's
    via pair then sits on a straight stretch, not on a corner where one trace would pass the other's via).
    no_via: [(x, y, r)] mm: no layer change within r of these points"""
    w = obs.win
    goal_set = {}
    for (x, y, L, d) in goals:
        i, j = w.ij(x, y)
        goal_set.setdefault((i, j, L), set()).add(d)
    gi = [(w.ij(x, y), L) for (x, y, L, d) in goals]

    def h(i, j):
        best = 1e18
        for (a, b), _ in gi:
            dx, dy = abs(a - i), abs(b - j)
            best = min(best, max(dx, dy) + 0.41421356 * min(dx, dy))
        return best * min(layer_cost.values())

    openq, gbest, parent, macro = [], {}, {}, {}
    nv = [(*w.ij(x, y), int(math.ceil(r / w.res))) for x, y, r in no_via]

    def via_ok(i, j):
        return all((i - a) ** 2 + (j - c) ** 2 > k * k for a, c, k in nv)
    for (x, y, L, d) in starts:
        i, j = w.ij(x, y)
        for dd in ([d] if d is not None else range(8)):
            s = (i, j, L, dd)
            gbest[s] = 0.0
            parent[s] = None
            heapq.heappush(openq, (h(i, j), 0.0, s))
    n = 0
    while openq:
        f, gcost, s = heapq.heappop(openq)
        if gcost > gbest.get(s, 1e18):
            continue
        i, j, L, d = s
        gd = goal_set.get((i, j, L))
        if gd is not None and (None in gd or d in gd):
            path = []
            while s is not None:
                path.append(s)
                path.extend(reversed(macro.get(s, ())))
                s = parent[s]
            path.reverse()
            return [(w.xy(i_, j_)[0], w.xy(i_, j_)[1], L_, d_) for (i_, j_, L_, d_) in path]
        n += 1
        if n > max_expand:
            astar.last = ('max_expand', n)
            return None
        # straight or 45 degree turns
        for dd, extra in ((d, 0.0), ((d + 1) % 8, turn_cost), ((d - 1) % 8, turn_cost)):
            di, dj = DIRS[dd]
            ni, nj = i + di, j + dj
            if not obs.free(L, ni, nj):
                continue
            step = (1.41421356 if di and dj else 1.0) * layer_cost[L] + extra
            t = (ni, nj, L, dd)
            ng = gcost + step
            if ng < gbest.get(t, 1e18):
                gbest[t] = ng
                parent[t] = s
                heapq.heappush(openq, (ng + h(ni, nj), ng, t))
        if allow_vias and via_straight > 0:
            di, dj = DIRS[d]
            K = via_straight
            pre = [(i + k * di, j + k * dj) for k in range(1, K + 1)]
            vi, vj = pre[-1]
            if all(obs.free(L, a, c) for a, c in pre) and obs.via_free(vi, vj) and via_ok(vi, vj):
                step = 1.41421356 if di and dj else 1.0
                for L2 in layer_cost:
                    post = [(vi + k * di, vj + k * dj) for k in range(0, K + 1)]
                    if L2 == L or not all(obs.free(L2, a, c) for a, c in post):
                        continue
                    ei, ej = post[-1]
                    t = (ei, ej, L2, d)
                    ng = gcost + via_cost + K * step * (layer_cost[L] + layer_cost[L2])
                    if ng < gbest.get(t, 1e18):
                        gbest[t] = ng
                        parent[t] = s
                        macro[t] = [(a, c, L, d) for a, c in pre] + [(a, c, L2, d) for a, c in post[:-1]]
                        heapq.heappush(openq, (ng + h(ei, ej), ng, t))
        elif allow_vias and obs.via_free(i, j) and via_ok(i, j):
            for L2 in layer_cost:
                if L2 == L or not obs.free(L2, i, j):
                    continue
                t = (i, j, L2, d)
                ng = gcost + via_cost
                if ng < gbest.get(t, 1e18):
                    gbest[t] = ng
                    parent[t] = s
                    heapq.heappush(openq, (ng + h(i, j), ng, t))
    astar.last = ('exhausted', n)
    return None


def simplify(path):
    """cells -> runs [(L, [(x, y), ...])]: one run per layer, corner points only"""
    runs = []
    for (x, y, L, d) in path:
        if not runs or runs[-1][0] != L:
            runs.append((L, [(x, y)], [d]))
        else:
            runs[-1][1].append((x, y))
            runs[-1][2].append(d)
    out = []
    for L, pts, ds in runs:
        keep = [pts[0]]
        for k in range(1, len(pts) - 1):
            if ds[k] != ds[k + 1]:
                keep.append(pts[k])
        if len(pts) > 1:
            keep.append(pts[-1])
        out.append((L, keep))
    return out


def offset_polyline(pts, off):
    """parallel polyline at signed distance off (left of travel = positive, y down), mitred corners"""
    if len(pts) < 2:
        return list(pts)
    res = []
    for k, p in enumerate(pts):
        if k == 0:
            a, b = pts[0], pts[1]
            nx, ny = _normal(a, b)
            res.append((p[0] + off * nx, p[1] + off * ny))
        elif k == len(pts) - 1:
            a, b = pts[-2], pts[-1]
            nx, ny = _normal(a, b)
            res.append((p[0] + off * nx, p[1] + off * ny))
        else:
            n1 = _normal(pts[k - 1], p)
            n2 = _normal(p, pts[k + 1])
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            ml = math.hypot(mx, my)
            mx, my = mx / ml, my / ml
            c = mx * n1[0] + my * n1[1]
            res.append((p[0] + off * mx / c, p[1] + off * my / c))
    return res


def _normal(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (dy / L, -dx / L)          # left of travel in a y-down frame


def add_track(board, net, L, pts, width, locked=True, add=True):
    """tracks along polyline pts (mm); add=False: built but not put on the board (for a check)"""
    items = []
    for a, b in zip(pts, pts[1:]):
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-4:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(nm(O + a[0]), nm(O + a[1])))
        t.SetEnd(pcbnew.VECTOR2I(nm(O + b[0]), nm(O + b[1])))
        t.SetWidth(nm(width))
        t.SetLayer(LAYER[L])
        t.SetNet(board.FindNet(net))
        t.SetLocked(locked)
        if add:
            board.Add(t)
        items.append(t)
    return items


def add_via(board, net, x, y, dia, drill, locked=True):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(nm(O + x), nm(O + y)))
    v.SetWidth(nm(dia))
    v.SetDrill(nm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(board.FindNet(net))
    v.SetLocked(locked)
    board.Add(v)
    return v


def clear_of(board, items, codes, clearance):
    """True when none of `items` (tracks / vias just added) comes closer than `clearance` mm to the copper (tracks,
    vias, pads) of the nets `codes`, measured with KiCad's own shapes (no grid): the exact check behind a rasterised
    search, for the gap inside a differential pair"""
    others = [t for t in tracks(board) if t.GetNetCode() in codes]
    others += [p for fp in footprints(board) for p in pads(fp) if p.GetNetCode() in codes]
    c = nm(clearance)
    for it in items:
        bb = it.GetBoundingBox()
        bb.Inflate(c + nm(1.0))
        for o in others:
            if not bb.Intersects(o.GetBoundingBox()):
                continue
            for L in LAYER.values():
                if it.IsOnLayer(L) and o.IsOnLayer(L) and it.GetEffectiveShape(L).Collide(o.GetEffectiveShape(L), c):
                    return False
            # via holes: 0.2 mm to the other side's copper (JLC via hole to track)
            for v, other in ((it, o), (o, it)):
                if isinstance(v, pcbnew.PCB_VIA):
                    for L in LAYER.values():
                        if other.IsOnLayer(L) and other.GetEffectiveShape(L).Collide(v.GetEffectiveHoleShape(), nm(0.2)):
                            return False
    return True
