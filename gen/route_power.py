"""Power distribution of Board A, laid down before the autorouter: copper pours (zones), via arrays between pours on
different layers, and wide trunk traces found with the grid router (gen/proute.py).

Current-carrying copper (JLC06121H-3313A: 1 oz finished outer, 0.5 oz inner; IPC-2152 rough figures for 20 C rise):
outer 1 oz ~ 3 A per 1.5 mm of width, inner 0.5 oz ~ 1 A per mm; one 0.2 mm via ~ 1 A.
"""
import math

import pcbnew

import proute as R

O = R.O


def nm(v):
    return pcbnew.FromMM(v)


def zone(b, net, layer, pts, prio=1, clearance=0.15, min_w=0.2, thermal=False, name=''):
    """copper pour; solid pad connection by default (power), thermal reliefs on request"""
    z = pcbnew.ZONE(b)
    z.SetLayer(R.LAYER[layer] if isinstance(layer, str) else layer)
    z.SetNet(b.FindNet(net))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(nm(clearance))
    z.SetMinThickness(nm(min_w))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL if thermal else pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(nm(0.2))
    z.SetThermalReliefSpokeWidth(nm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(nm(O + x), nm(O + y))
    b.Add(z)
    return z


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def inside(pts, x, y):
    c = False
    n = len(pts)
    for k in range(n):
        (ax, ay), (bx, by) = pts[k], pts[(k + 1) % n]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c


def stitch(b, net, pts, pitch=0.8, via=(0.4, 0.2), clearance=0.15, limit=None, res=0.025):
    """vias of `net` on a grid inside polygon pts, wherever they clear every other net on every layer"""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    win = R.Window(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1, res)
    code = b.FindNet(net).GetNetCode()
    obs = R.Obstacles(b, win, {code}, 0.05, clearance, via_r=via[0] / 2)
    # the net's own vias are not obstacles above, but holes must keep their distance from them too
    own = [R.to_mm(t.GetPosition()) for t in R.tracks(b) if isinstance(t, pcbnew.PCB_VIA) and t.GetNetCode() == code]
    placed = []
    step = pitch / 3                      # fine candidate grid, vias kept `pitch` apart
    y = min(ys) + via[0] / 2
    while y < max(ys) and not (limit and len(placed) >= limit):
        x = min(xs) + via[0] / 2
        while x < max(xs):
            if inside(pts, x, y) and obs.via_free(*win.ij(x, y)) and \
                    all(math.hypot(x - px, y - py) >= pitch * 0.99 for px, py in placed) and \
                    all(math.hypot(x - px, y - py) >= via[0] + 0.25 for px, py in own):
                placed.append((x, y))
                if limit and len(placed) >= limit:
                    break
            x += step
        y += step
    for x, y in placed:
        R.add_via(b, net, x, y, via[0], via[1])
    return len(placed)


def trunk(b, net, a, z, width, layers=('F', 'In3', 'B'), clearance=0.15, margin=6.0, cost=None, vias_per_hop=3,
          via=(0.4, 0.2), res=None):
    """wide trace from a = (x, y, layer) to z = (x, y, layer); at every layer change a cluster of vias.
    Returns the length routed (mm) or None"""
    xs, ys = [a[0], z[0]], [a[1], z[1]]
    if res is None:                                # long trunks on a coarser grid (search budget), wide ones anyway
        res = 0.05 if math.dist(a[:2], z[:2]) < 20 and width < 0.8 else 0.1
    win = R.Window(min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin, res)
    code = b.FindNet(net).GetNetCode()
    half = width / 2
    vr = via[0] / 2 + 0.55                         # room for the via cluster (offsets 0.55)
    obs = R.Obstacles(b, win, {code}, half, clearance, via_r=vr, layers=tuple(R.ROUTE_LAYERS), escapes='all')
    # neck: within NECK mm of a fine-pitch end the trunk narrows to that pad's width (a 1 mm trunk cannot leave a
    # 0.25 mm pin at 0.5 mm pitch); the narrow grid replaces the wide one inside those disks
    necks = [(e, nw) for e, nw in ((a, neck_w(b, a)), (z, neck_w(b, z))) if nw and nw < width]
    if necks:
        obs_n = R.Obstacles(b, win, {code}, min(nw for _, nw in necks) / 2, clearance, layers=tuple(R.ROUTE_LAYERS),
                            escapes='all')
        k = int(NECK / res)                        # within NECK only: what is drawn narrow is a superset (below)
        for e, _ in necks:
            ci, cj = win.ij(e[0], e[1])
            for L in R.ROUTE_LAYERS:
                for j in range(max(0, cj - k), min(win.ny, cj + k + 1)):
                    for i in range(max(0, ci - k), min(win.nx, ci + k + 1)):
                        if (i - ci) ** 2 + (j - cj) ** 2 <= k * k:
                            obs.g[L][j * win.nx + i] = obs_n.g[L][j * win.nx + i]
    for L in R.ROUTE_LAYERS:
        if L not in layers:
            obs.g[L] = bytearray(b'\x01' * len(obs.g[L]))
    for L in layers:
        obs.clear_disk(L, a[0], a[1], 0.0)
        obs.clear_disk(L, z[0], z[1], 0.0)
    lc = cost or {L: (1.0 if L in ('F', 'B') else 1.3) for L in layers}
    path = R.astar(obs, [(a[0], a[1], a[2], None)], [(z[0], z[1], z[2], None)], lc, via_cost=2.0 / res,
                   turn_cost=0.3, max_expand=12_000_000)
    if path is None:
        return None
    runs = R.simplify(path)
    total = 0.0
    placed = []                                    # this trunk's vias: clusters of close layer changes keep apart
    for k, (L, p) in enumerate(runs):
        p = list(p)
        # the path runs on cell centres: a short stub to the exact end (inside its pad), rather than moving the last
        # segment's end, which turns the whole segment toward the neighbouring pins
        if k == 0 and math.dist(p[0], a[:2]) > 1e-4:
            p.insert(0, (a[0], a[1]))
        if k == len(runs) - 1 and math.dist(p[-1], z[:2]) > 1e-4:
            p.append((z[0], z[1]))
        for piece, w in _neck_pieces(p, necks, width):
            R.add_track(b, net, L, piece, w)
        total += sum(math.dist(u, v) for u, v in zip(p, p[1:]))
        if k < len(runs) - 1:
            cx, cy = p[-1]
            for dx, dy in [(0, 0), (0.55, 0), (-0.55, 0), (0, 0.55), (0, -0.55)][:vias_per_hop]:
                v = (cx + dx, cy + dy)
                if (dx or dy) and any(math.dist(v, q) < via[1] + 0.22 for q in placed):
                    continue                       # hole to hole 0.2 mm (+ margin)
                R.add_via(b, net, v[0], v[1], via[0], via[1])
                placed.append(v)
    return total


NECK = 1.3          # mm around a fine-pitch trunk end where the trunk runs at the pad's width


def neck_w(b, end):
    """width a trunk may have at this end: 0.9 x the pad's smaller side for pins narrower than 0.9 mm, else None"""
    best = None
    for fp in R.footprints(b):
        for p in R.pads(fp):
            q = R.to_mm(p.GetPosition())
            if abs(q[0] - end[0]) < 1e-3 and abs(q[1] - end[1]) < 1e-3:
                bb = p.GetBoundingBox()
                m = min(pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))
                if m < 0.9:
                    best = round(max(0.2, m * 0.9), 2)
    return best


def _neck_pieces(p, necks, width):
    """split polyline p into pieces at the neck circles: narrow within NECK + half the width of an end (so the full-width
    copper, round end included, stays where the search checked it at full width), full width outside; at a boundary
    the narrow piece takes the boundary segment"""
    def wid(pt):
        for e, nw in necks:
            if math.dist(pt, e[:2]) <= NECK + width / 2 + 0.03:
                return nw
        return width
    pts = [p[0]]
    for u, v in zip(p, p[1:]):                      # densify, then group consecutive points by width
        n = max(1, int(math.dist(u, v) / 0.05))
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
    res = []
    for piece, w in out:                            # back to corner points only
        keep = [piece[0]] + [piece[i] for i in range(1, len(piece) - 1)
                             if abs((piece[i][0] - piece[i - 1][0]) * (piece[i + 1][1] - piece[i][1]) -
                                    (piece[i][1] - piece[i - 1][1]) * (piece[i + 1][0] - piece[i][0])) > 1e-9] + [piece[-1]]
        if len(keep) >= 2:
            res.append((keep, w))
    return res


def pad(b, ref_pad):
    ref, num = ref_pad.split('.')
    fp = b.FindFootprintByReference(ref)
    for p in R.pads(fp):
        if p.GetNumber() == num:
            return fp, p
    raise KeyError(ref_pad)


def hull_zone(b, net, layer, pads, margin=0.25, prio=5, name=''):
    """pour over the convex hull of the listed pads (their copper, inflated by margin): a local power-loop or
    switch-node copper area. Other nets inside the hull are cleared by the zone fill."""
    pts = []
    for rp in pads:
        _, p = pad(b, rp)
        ps = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(ps, R.LAYER[layer], nm(margin), nm(0.005), pcbnew.ERROR_OUTSIDE)
        for k in range(ps.OutlineCount()):
            o = ps.Outline(k)
            pts += [R.to_mm(o.CPoint(i)) for i in range(o.PointCount())]
    h = _hull(pts)
    # '(hull)': a small switch-node / loop pour: the grid router keeps other nets' vias out of it (one could split it)
    return zone(b, net, layer, h, prio=prio, name=name or f'{net.split("/")[-1]} {layer} (hull)'), h


def _hull(pts):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, c):
        return (a[0] - o[0]) * (c[1] - o[1]) - (a[1] - o[1]) * (c[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def full(b, short):
    for n in R.net_names(b):
        if str(n).split('/')[-1] == short:
            return str(n)
    raise KeyError(short)


# ------------------------------------------------------------------------------------------------ the plan
# pours: (net, layer, pads or rect, margin / priority). Switch nodes and loop nodes of every power stage are hull
# pours over their pads; the battery path and the CM5 input are rectangles (12 A / 6 A paths).
STAGE_HULLS = [
    # BQ25713 charger (bottom). The bootstrap capacitors' SW pads are joined by a short track instead: a hull over them
    # reached up to the controller's gate-drive row and closed the channel its eight drive / bootstrap pins leave by
    ('CHG_SW1', 'B', ['Q101.1', 'Q101.2', 'Q101.3', 'Q102.5', 'Q102.6', 'Q102.7', 'Q102.8', 'Q102.9', 'L101.1']),
    ('CHG_SW2', 'B', ['Q103.5', 'Q103.6', 'Q103.7', 'Q103.8', 'Q103.9', 'Q104.1', 'Q104.2', 'Q104.3', 'L101.2']),
    ('CHG_IN_S', 'B', ['R108.2', 'C116.1', 'C117.1', 'Q101.5', 'Q101.6', 'Q101.7', 'Q101.8', 'Q101.9']),
    ('CHG_IN', 'B', ['R108.1', 'C110.1', 'C111.1', 'C112.1', 'C113.1', 'C115.1']),
    ('VSYS', 'B', ['Q104.5', 'Q104.6', 'Q104.7', 'Q104.8', 'Q104.9', 'C120.1', 'C121.1', 'C122.1', 'C123.1', 'C124.1',
                   'C125.1', 'C126.1', 'C127.1']),
    # TPS61088 -> CM5_VIN (bottom)
    ('BST_CM5_SW', 'B', ['U201.4', 'U201.5', 'U201.6', 'U201.7', 'L201.2', 'C204.2']),
    # TPS61089 -> 5 V (top)
    ('BST_5V_SW', 'F', ['U202.11', 'L202.2', 'C214.2']),
    ('VCC5V0', 'F', ['U202.6', 'C216.1', 'C217.1', 'C218.1', 'C219.1']),
    ('VSYS', 'F', ['L202.1', 'C211.1']),
    # TPS63020 LTE / AUX (bottom)
    ('BB_LTE_L1', 'B', ['U203.8', 'U203.9', 'L203.1']),
    ('BB_LTE_L2', 'B', ['U203.6', 'U203.7', 'L203.2']),
    ('VSYS', 'B', ['U203.10', 'U203.11', 'C221.1', 'C222.1']),
    ('VCC_LTE', 'B', ['U203.4', 'U203.5', 'C223.1', 'C224.1', 'C225.1']),
    ('BB_AUX_L1', 'B', ['U204.8', 'U204.9', 'L204.1']),
    ('BB_AUX_L2', 'B', ['U204.6', 'U204.7', 'L204.2']),
    ('VCC3V3_AUX', 'B', ['U204.4', 'U204.5', 'C229.1', 'C230.1', 'C231.1']),
]
RECTS = [
    # battery path, 12 A: connector pins on the top, sense resistor / BATFET on the bottom, via arrays between
    ('BAT_P', 'F', (65.9, 7.5, 74.2, 11.3)), ('BAT_P', 'B', (64.85, 5.2, 68.75, 13.9)),
    ('BAT_SRP', 'B', (68.9, 8.2, 75.6, 13.65)),
    ('BAT_N', 'F', (58.4, 7.5, 65.6, 11.3)), ('BAT_N', 'B', (62.6, 6.6, 64.7, 12.4)),
    # BATFET drain -> CM5 boost and AUX buck-boost inputs
    ('VSYS', 'B', (62.3, 14.4, 76.2, 23.4)),
    # CM5 input: boost output capacitors on the bottom, connector A VIN pins on the top
    # (the display FPC's DSI_D0 / D1 / CLK breakout vias pass through this pour: it is filled around them)
    ('CM5_VIN', 'B', (51.95, 23.6, 56.4, 31.4), 'vias pass'),
]
POLYS = [   # (net, layer, polygon)
    # CM5 VBUS pins 77-87 (JP1, y 26.87-28.87) and the via array right beside them; 0.15 mm from the pins
    # above and below (89 and 75 unused)
    ('CM5_VIN', 'F', [(50.55, 26.72), (53.3, 26.72), (53.3, 29.02), (50.55, 29.02)]),
]
# VSYS on L4: a band over the BATFET and the converter inputs (y 13.8-24.5, 10.7 mm: ~10 A at 0.5 oz by the rough
# figure above) with a tab over the backlight / 5 V boost feed vias (x 70-77, to y 27.6), and one down the right side
# to the charger output (x 84-92.3, 8.3 mm: ~8 A); the rest of L4 under the power section stays free for the signals
# that cross it, the charger controller's included (D76: the band went to y 29 before)
VSYS_L4 = [(56.0, 13.8), (92.3, 13.8), (92.3, 46.8), (84.0, 46.8), (84.0, 24.5), (77.0, 24.5), (77.0, 27.6),
           (70.0, 27.6), (70.0, 24.5), (56.0, 24.5)]
STITCH = [   # (net, rect, max vias): via arrays joining the pours of a net on different layers
    ('BAT_P', (65.0, 7.6, 68.7, 11.2), 18), ('BAT_N', (62.7, 7.6, 64.6, 11.3), 12), ('GND', (55.8, 6.8, 59.3, 13.0), 14),
    ('CM5_VIN', (51.75, 26.8, 53.25, 28.95), 10),
    ('VSYS', (62.5, 14.6, 76.0, 23.2), 18), ('VSYS', (82.6, 40.0, 91.2, 43.4), 10), ('VSYS', (70.6, 25.4, 77.0, 27.0), 6),
]


def zones_and_vias(b, log=print):
    for net, L, pads in STAGE_HULLS:
        hull_zone(b, full(b, net), L, pads)
    for net, L, (x0, y0, x1, y1), *tag in RECTS:
        zone(b, full(b, net), L, rect(x0, y0, x1, y1), prio=4, name=f'{net} {L}' + (f' ({tag[0]})' if tag else ''))
    for net, L, pts in POLYS:
        zone(b, full(b, net), L, pts, prio=4, name=f'{net} {L}')
    zone(b, full(b, 'VSYS'), 'In3', VSYS_L4, prio=2, name='VSYS L4')
    for net, (x0, y0, x1, y1), n in STITCH:
        k = stitch(b, full(b, net), rect(x0, y0, x1, y1), pitch=0.75, limit=n)
        log(f'stitch {net} {x0},{y0}: {k} vias')


TRUNKS = [   # (net, from pad, to pad, width mm, layers): long power runs, after the differential pairs
    ('CHG_IN', 'R108.1', 'U101.20', 1.2, ('F', 'In3', 'B')),           # USB-C power path -> charger input, 3 A
    ('VSYS', 'Q105.9', 'C221.1', 1.2, ('F', 'In3', 'B')),              # -> LTE buck-boost input (2.5 A)
    ('VSYS', 'C221.1', 'U106.3', 0.4, ('F', 'In3', 'B')),
    ('VSYS', 'L201.1', 'U801.7', 1.0, ('F', 'In3', 'B')),              # -> speaker amplifiers (2 x 1.2 A peak)
    ('VSYS', 'U801.7', 'U802.7', 0.8, ('F', 'In3', 'B')),
    ('VCC_LTE', 'C225.1', 'C504.1', 1.2, ('B', 'In3')),                # LTE output -> 220 uF bulk
    ('VCC_LTE', 'C504.1', 'C503.1', 1.2, ('B', 'In3')),
    ('VCC_LTE', 'C223.1', 'C505.1', 1.2, ('B', 'In3')),                # -> MLCC array at VCC pins 70-74
    ('VCC_LTE', 'C503.1', 'C509.1', 1.2, ('B', 'In3')),                # -> MLCC array at VCC pins 2/4
    ('VCC5V0', 'C219.1', 'U402.1', 1.0, ('F', 'B')),                   # 5 V -> USB-A power switches
    ('VCC5V0', 'C219.1', 'U403.1', 1.0, ('F', 'B')),
    ('VCC5V0', 'C219.1', 'U1001.1', 0.5, ('F', 'In2', 'B')),            # -> keyboard power switch (0.5 A)
    ('VCC5V0', 'U1001.1', 'R715.1', 0.4, ('F', 'In2', 'B')),            # -> rear camera 5 V
    ('VCC3V3_AUX', 'C229.1', 'U401.36', 0.5, ('F', 'In2', 'B')),        # AUX 3.3 V -> USB hub
    ('VCC3V3_AUX', 'C229.1', 'FB601.1', 0.5, ('F', 'In2', 'B')),        # -> Wi-Fi (0.6 A TX peaks)
    ('VCC3V3_AUX', 'FB601.1', 'FB703.1', 0.4, ('F', 'In2', 'B')),       # -> cameras
    ('VCC3V3_AUX', 'FB703.1', 'FB702.1', 0.4, ('F', 'In2', 'B')),
]


def trunks(b, log=print):
    failed = []
    for net, a, z, w, layers in TRUNKS:
        fa, pa = pad(b, a)
        fz, pz = pad(b, z)
        A = R.to_mm(pa.GetPosition()) + ('B' if fa.IsFlipped() else 'F',)
        Z = R.to_mm(pz.GetPosition()) + ('B' if fz.IsFlipped() else 'F',)
        n = full(b, net)
        L = trunk(b, n, A, Z, w, layers=layers)
        if L is None:                                    # a wider search window, same width
            L = trunk(b, n, A, Z, w, layers=layers, margin=15.0)
        if L is None:
            L = trunk(b, n, A, Z, w * 0.7, layers=('F', 'In2', 'In3', 'B'), margin=15.0)
            w *= 0.7
        log(f'trunk {net} {a} -> {z}: ' + ('FAILED' if L is None else f'{L:.1f} mm at {w:.2f} mm'))
        if L is None:
            failed.append((net, a, z))
    return failed


def gnd_pours(b, log=print):
    """GND on the outer layers wherever nothing else is (lowest priority), joined to the L2 / L5 planes by a stitching
    grid; the planes themselves are added at the start (gen/route_a.py)"""
    e = 0.3
    outline = rect(e, e, 95.0 - e, 65.0 - e)
    gnd = full(b, 'GND')
    for L in ('F', 'B'):
        zone(b, gnd, L, outline, prio=0, clearance=0.2, min_w=0.2, thermal=True, name=f'GND {L}')
    n = stitch(b, gnd, outline, pitch=2.5, via=(0.4, 0.2), clearance=0.2, res=0.05)
    log(f'GND stitching: {n} vias')
    return n
